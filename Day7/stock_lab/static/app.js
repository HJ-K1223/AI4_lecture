"use strict";

const $ = (id) => document.getElementById(id);
const labels = { bad: "동기 호출 · 서버 정지", good: "비동기 조회 · 양보", thread: "동기 조회 · 스레드 위임" };
const products = ["데일리 머그", "포켓 노트", "캔버스 백"];
let running = false;
let history = [];
const seconds = (ms) => (ms / 1000).toFixed(2);

function cell(row, value) {
  const td = document.createElement("td");
  td.textContent = value;
  row.append(td);
}

async function getJSON(path) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(path, { cache: "no-store", signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

function lock(value) {
  running = value;
  document.querySelectorAll("button, input[name=mode]").forEach((el) => { el.disabled = value; });
}

function renderHistory() {
  $("history").replaceChildren();
  if (!history.length) {
    const row = document.createElement("tr");
    cell(row, "실험 기록이 여기에 쌓입니다. 새로고침하면 초기화됩니다.");
    row.firstChild.colSpan = 4;
    row.firstChild.className = "empty";
    $("history").append(row);
    return;
  }
  for (const item of history) {
    const row = document.createElement("tr");
    [labels[item.mode], `${item.count}개`, `${seconds(item.elapsed)}초`, item.health].forEach((v) => cell(row, v));
    $("history").append(row);
  }
}

function renderTimeline(results, mode) {
  $("timeline").replaceChildren();
  if (!results.length) {
    $("timeline").textContent = "조회 실패로 표시할 서버 기록이 없습니다.";
    return;
  }
  const origin = Math.min(...results.map((r) => r.data.lookup_started));
  const span = Math.max(6, ...results.map((r) => r.data.lookup_finished - origin));
  results.sort((a, b) => a.id - b.id);
  for (const { id, data } of results) {
    const row = document.createElement("div");
    row.className = "timeline-row";
    const title = document.createElement("span");
    title.textContent = products[id - 1];
    const track = document.createElement("div");
    track.className = "track";
    const bar = document.createElement("div");
    bar.className = `bar ${mode}`;
    const start = data.lookup_started - origin;
    const duration = data.lookup_finished - data.lookup_started;
    bar.style.left = `${start / span * 100}%`;
    bar.style.width = `${duration / span * 100}%`;
    bar.textContent = `${duration.toFixed(2)}초`;
    bar.title = `조회 시작 +${start.toFixed(3)}초 / 종료 +${(start + duration).toFixed(3)}초`;
    track.append(bar);
    const thread = document.createElement("span");
    thread.className = "thread-label";
    thread.textContent = `${data.lookup_thread.name} / ${data.lookup_thread.id}`;
    row.append(title, track, thread);
    $("timeline").append(row);
  }
  const axis = document.createElement("div");
  axis.className = "axis";
  for (let i = 0; i <= 6; i++) {
    const tick = document.createElement("span");
    tick.textContent = `${(span * i / 6).toFixed(1)}s`;
    axis.append(tick);
  }
  $("timeline").append(axis);
}

async function experiment(mode, count) {
  const batchStart = performance.now();
  const results = [];
  let finished = 0;
  $("run-state").textContent = `${labels[mode]} · 진행 중`;
  $("explanation").textContent = "조회 중입니다. 화면의 시간은 브라우저에서 측정하며 서버가 멈춰도 계속 움직입니다.";
  $("timeline").textContent = "서버 조회 기록을 기다리고 있습니다…";
  $("request-details").replaceChildren();
  $("request-count").innerHTML = `${count}<small>개</small>`;
  $("health-time").innerHTML = `대기<small>중</small>`;
  for (let id = 1; id <= 3; id++) {
    $("stock-" + id).className = `stock${id <= count ? " pending" : ""}`;
    $("stock-" + id).textContent = id <= count ? "조회 중…" : "이번 조회 제외";
    $("timing-" + id).textContent = id <= count ? "서버 응답을 기다리고 있어요." : "상품 3개 조회로 함께 비교하세요.";
  }
  const clock = setInterval(() => {
    $("total-time").innerHTML = `${seconds(performance.now() - batchStart)}<small>초</small>`;
  }, 80);

  // 상품 요청이 서버에 진입한 뒤 별도의 가벼운 API도 응답할 수 있는지 관찰합니다.
  // 성공/실패를 값으로 돌려주므로 상품 요청을 기다리는 동안 미처리 rejection이 생기지 않습니다.
  const healthTask = new Promise((resolve) => setTimeout(resolve, 300)).then(async () => {
    const start = performance.now();
    try {
      await getJSON("/health");
      const text = `${seconds(performance.now() - start)}초`;
      $("health-time").textContent = text;
      return text;
    } catch (error) {
      $("health-time").textContent = "실패";
      return `실패 (${error.name === "AbortError" ? "20초 초과" : error.message})`;
    }
  });

  // map 중 fetch를 모두 호출한 후 Promise.allSettled로 함께 기다립니다.
  // for문 안에서 요청마다 await하는 순차 클라이언트가 아닙니다.
  const tasks = Array.from({ length: count }, (_, index) => {
    const id = index + 1;
    const started = performance.now();
    return getJSON(`/api/stock/${mode}/${id}`).then((data) => {
      const elapsed = performance.now() - started;
      $("stock-" + id).className = "stock ready";
      $("stock-" + id).textContent = `재고 ${data.product.stock}개`;
      $("timing-" + id).textContent = `HTTP 200 · 응답 대기 ${seconds(elapsed)}초`;
      results.push({ id, data });
      const row = document.createElement("tr");
      [products[id - 1], `+${(started - batchStart).toFixed(1)}ms`, `${seconds(elapsed)}초`,
        `${data.endpoint_thread.name} / ${data.endpoint_thread.id}`,
        `${data.lookup_thread.name} / ${data.lookup_thread.id}`].forEach((v) => cell(row, v));
      $("request-details").append(row);
    }).catch((error) => {
      $("stock-" + id).className = "stock error";
      $("stock-" + id).textContent = "조회 실패";
      $("timing-" + id).textContent = error.name === "AbortError" ? "20초 제한을 초과했어요." : error.message;
      throw error;
    }).finally(() => { finished++; });
  });

  let settled;
  let elapsed;
  try {
    settled = await Promise.allSettled(tasks);
    elapsed = performance.now() - batchStart;
  } finally {
    clearInterval(clock);
  }
  $("total-time").innerHTML = `${seconds(elapsed)}<small>초</small>`;
  const health = await healthTask;
  renderTimeline(results, mode);
  const failures = settled.filter((item) => item.status === "rejected").length;
  const notes = {
    bad: "동기 보조 함수의 sleep이 이벤트 루프 스레드를 멈춥니다. 상품들의 조회 구간이 차례로 이어지는지 확인하세요.",
    good: "같은 이벤트 루프 스레드에서 실행하지만, await 중에는 다른 요청을 진행합니다. 상품들의 대기 구간이 겹치는지 확인하세요.",
    thread: "엔드포인트는 이벤트 루프에, 동기 조회는 별도 스레드에 있습니다. 조회 스레드 ID와 구간의 겹침을 확인하세요."
  };
  $("explanation").textContent = failures ? `${count}개 중 ${failures}개 조회 실패. 서버 터미널과 연결 상태를 확인하세요.` : notes[mode];
  $("run-state").textContent = `${finished}개 완료${failures ? ` · ${failures}개 실패` : ""}`;
  history.unshift({ mode, count, elapsed, health });
  history = history.slice(0, 30);
  renderHistory();
}

async function run(all, count) {
  if (running) return;
  lock(true);
  try {
    const selected = document.querySelector("input[name=mode]:checked").value;
    for (const mode of all ? ["bad", "good", "thread"] : [selected]) {
      document.querySelector(`input[value="${mode}"]`).checked = true;
      await experiment(mode, count);
    }
  } catch (error) {
    $("run-state").textContent = "실험을 완료하지 못했어요";
    $("explanation").textContent = `오류: ${error.message}. 서버 실행 상태를 확인하세요.`;
  } finally {
    lock(false);
  }
}

$("run-three").addEventListener("click", () => run(false, 3));
$("run-one").addEventListener("click", () => run(false, 1));
$("run-all").addEventListener("click", () => run(true, 3));
$("clear-history").addEventListener("click", () => { history = []; renderHistory(); });
