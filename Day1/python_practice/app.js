"use strict";

// 브라우저용 동작 예제입니다. Python 파일을 실행하거나 해석하지 않습니다.
function integer(value, min = Number.MIN_SAFE_INTEGER, max = Number.MAX_SAFE_INTEGER) {
  if (String(value).trim() === "") throw new Error("빈칸에 정수를 입력하세요.");
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number < min || number > max) {
    throw new Error(`${min}~${max} 사이의 정수를 입력하세요.`);
  }
  return number;
}

function listResult(values) {
  const evens = values.filter(value => value % 2 === 0);
  return `[${values.join(", ")}]\n짝수: ${evens.length ? evens.join(", ") : "없음"}`;
}

function tableResult(start, end, limit) {
  if (start > end) throw new Error("시작 단은 마지막 단보다 작거나 같아야 합니다.");
  const rows = [];
  for (let multiplier = 1; multiplier <= limit; multiplier++) {
    const row = [];
    for (let table = start; table <= end; table++) {
      row.push(`${table} x ${multiplier} = ${table * multiplier}`);
    }
    rows.push(row.join("    "));
  }
  return rows.join("\n");
}

function createGame(random = Math.random) {
  const target = Math.floor(random() * 100) + 1;
  let count = 0;
  let done = false;
  return {
    guess(value) {
      if (done) throw new Error("새 게임을 시작하세요.");
      const number = integer(value, 1, 100);
      count++;
      done = number === target;
      const message = done ? `정답입니다! 총 시도 횟수: ${count}`
        : number > target ? "컴퓨터보다 큽니다. 더 작은 숫자를 입력하세요."
          : "컴퓨터보다 작습니다. 더 큰 숫자를 입력하세요.";
      return {count, done, message: `${count}회 · ${number} → ${message}`};
    }
  };
}

function init() {
  function show(id, message, error = false) {
    const element = document.getElementById(id);
    element.textContent = message;
    element.classList.toggle("error", error);
  }
  function bind(formId, outputId, run) {
    document.getElementById(formId).addEventListener("submit", event => {
      event.preventDefault();
      try {
        const data = new FormData(event.currentTarget);
        show(outputId, run(data));
      } catch (error) {
        show(outputId, error.message, true);
      }
    });
  }
  bind("sum-form", "sum-result", data => {
    const a = integer(data.get("first"));
    const b = integer(data.get("second"));
    if (!Number.isSafeInteger(a + b)) throw new Error("계산 결과가 너무 큽니다. 더 작은 정수를 입력하세요.");
    return `number1 + number2 = ${a + b}`;
  });
  bind("score-form", "score-result", data => integer(data.get("score"), 0, 100) >= 60 ? "합격" : "불합격");
  bind("list-form", "list-result", data => listResult([1, 2, 3, 4, 5].map(i => integer(data.get(`n${i}`)))));
  bind("table-form", "table-result", data => tableResult(integer(data.get("start"), 1, 9), integer(data.get("end"), 1, 9), integer(data.get("limit"), 1, 9)));

  let game = createGame();
  let history = [];
  bind("game-form", "game-result", data => {
    const result = game.guess(data.get("guess"));
    history.push(result.message);
    document.getElementById("attempts").textContent = `${result.count}회 시도`;
    document.getElementById("guess-button").disabled = result.done;
    const input = document.querySelector('[name="guess"]');
    input.disabled = result.done;
    if (!result.done) { input.value = ""; input.focus(); }
    return history.join("\n");
  });
  document.getElementById("restart").addEventListener("click", () => {
    game = createGame();
    history = [];
    document.getElementById("game-form").reset();
    document.getElementById("guess-button").disabled = false;
    const input = document.querySelector('[name="guess"]');
    input.disabled = false;
    document.getElementById("attempts").textContent = "0회 시도";
    show("game-result", "새 숫자를 골랐습니다. 첫 번째 숫자를 입력하세요.");
    input.focus();
  });
  document.querySelectorAll("[data-answer]").forEach(element => {
    const index = Number(element.dataset.answer) - 1;
    element.textContent = (index === 4 ? "import random\n\n" : "") + PYTHON_ANSWERS[index];
  });
}

if (typeof document !== "undefined") init();
if (typeof module !== "undefined") module.exports = {integer, listResult, tableResult, createGame};
