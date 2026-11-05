Add-Type -AssemblyName System.Drawing
$outDir = $PSScriptRoot
$fontPath = 'C:\Windows\Fonts\malgun.ttf'
$fontCollection = New-Object System.Drawing.Text.PrivateFontCollection
$fontCollection.AddFontFile($fontPath)
$family = $fontCollection.Families[0]
$titleFont = New-Object System.Drawing.Font($family, 27, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$bodyFont = New-Object System.Drawing.Font($family, 22, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$smallFont = New-Object System.Drawing.Font($family, 18, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$ink = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#16324F'))
$muted = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#53667A'))
$blue = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#EDF5FF'))
$green = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#EAF7EF'))
$border = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#B8CEE7'), 2)
$arrow = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#6385A8'), 3)
$arrow.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap(5, 6)
$center = New-Object System.Drawing.StringFormat
$center.Alignment = [System.Drawing.StringAlignment]::Center
$center.LineAlignment = [System.Drawing.StringAlignment]::Center

function Draw-Diagram($file, $title, $subtitle, $nodes, $note) {
    $height = 190 + $nodes.Count * 120 + 70
    $bitmap = New-Object System.Drawing.Bitmap(800, $height)
    $g = [System.Drawing.Graphics]::FromImage($bitmap)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.Clear([System.Drawing.Color]::White)
    $g.DrawString($title, $titleFont, $ink, [System.Drawing.RectangleF]::new(30, 24, 740, 48), $center)
    $g.DrawString($subtitle, $smallFont, $muted, [System.Drawing.RectangleF]::new(35, 78, 730, 45), $center)
    for ($i = 0; $i -lt $nodes.Count; $i++) {
        $y = 145 + $i * 120
        $fill = $blue
        if ($i -eq $nodes.Count - 1) { $fill = $green }
        $rect = [System.Drawing.Rectangle]::new(65, $y, 670, 88)
        $g.FillRectangle($fill, $rect)
        $g.DrawRectangle($border, $rect)
        $g.DrawString($nodes[$i], $bodyFont, $ink, [System.Drawing.RectangleF]::new(80, $y + 3, 640, 82), $center)
        if ($i -lt $nodes.Count - 1) { $g.DrawLine($arrow, 400, $y + 92, 400, $y + 114) }
    }
    $g.DrawString($note, $smallFont, $muted, [System.Drawing.RectangleF]::new(40, $height - 99, 720, 75), $center)
    $bitmap.Save((Join-Path $outDir $file), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bitmap.Dispose()
}

Draw-Diagram 'main.png' 'main.py | Redis 기본 명령' '메시지 저장부터 만료·삭제까지' @(
    'Python에서 고유 키와 메시지 생성',
    'Redis String에 SET → GET·TTL 확인',
    'TTL 2초로 다시 저장',
    '3초 후 조회 → 만료로 데이터 없음',
    '다시 저장 → DEL로 삭제 → 결과 확인'
) 'String 값의 저장·조회와 키의 수명을 확인하는 실습'

Draw-Diagram 'main2.png' 'main2.py | Redis 자료형 비교' '데이터 모양에 따라 저장 방식을 선택' @(
    'Python에서 예제 데이터 준비',
    "Redis에 자료형별 저장`nString: 상태 / Hash: 프로필 / List: 메시지",
    "자료형에 맞는 명령으로 조회`nGET / HGET·HGETALL / LRANGE",
    '조회 결과·자료형·잘못된 명령의 오류 확인',
    '이번 실행에서 만든 실습 키 삭제'
) '각 키에 TTL 60초 설정 · 실행 종료 시 실습 키 정리'

Draw-Diagram 'main3.png' 'main3.py | 세션 관리' '세션 ID로 서버에 저장된 사용자를 확인' @(
    'create: 사용자 ID 입력 → 세션 ID 생성',
    "Redis String에 저장`n세션 ID → 사용자 ID / TTL 60초",
    'get: 입력한 세션 ID로 Redis 조회',
    '유효하면 사용자·TTL 출력 / 없으면 접근 거절',
    'logout으로 삭제 또는 60초 후 자동 만료'
) '세션을 조회해도 유효 시간은 연장되지 않음'

Draw-Diagram 'main4.png' 'main4.py | 세션별 대화 이력' '이전 대화를 읽어 규칙 기반 응답에 활용' @(
    '세션 ID + 질문 입력 → Redis에서 세션 확인',
    'Redis List에서 이전 대화 조회',
    '이전 대화 + 현재 질문 → 모의 응답 생성',
    '질문·응답을 JSON으로 변환 → List에 추가',
    '최근 6개 유지 → 이력 TTL 300초 갱신',
    '생성한 응답 출력'
) "실제 LLM API 호출 없음`n세션 TTL은 생성 후 300초이며 대화해도 연장되지 않음"

Draw-Diagram 'main5.png' 'main5.py | 원본 DB와 캐시' 'SQLite는 원본 · Redis는 임시 조회 결과' @(
    'history: 사용자 ID로 이력 요청',
    'Redis에서 사용자별 캐시 조회',
    "HIT: 캐시 사용`nMISS: SQLite에서 최근 6개 조회",
    'MISS일 때 Redis String에 JSON 저장 / TTL 60초',
    '캐시 또는 원본에서 가져온 이력 출력'
) "evict → Redis 캐시만 삭제 / SQLite 원본 유지`n현재 코드는 최신 메시지부터 출력"

Draw-Diagram 'main6.png' 'main6.py | 원본 저장과 캐시 갱신' 'SQLite 최신 메시지 ID를 캐시 버전으로 사용' @(
    'add: SQLite에 질문·모의 응답 저장 후 커밋',
    '이전 버전의 Redis 캐시 삭제',
    'history: SQLite에서 최신 ID 확인 → 버전 키 생성',
    "해당 버전 캐시 HIT → 캐시 사용`nMISS → SQLite에서 최근 6개 조회",
    'MISS일 때 시간순 정렬 → 새 버전 캐시 저장',
    '대화 이력 출력'
) "새 버전 캐시 TTL 60초 / HIT도 버전 확인 SQL 실행`nadd 이후 다음 history 요청이 캐시를 조회·복원"

$titleFont.Dispose()
$bodyFont.Dispose()
$smallFont.Dispose()
$fontCollection.Dispose()
Get-ChildItem -LiteralPath $outDir -Filter '*.png' | Select-Object Name, Length
