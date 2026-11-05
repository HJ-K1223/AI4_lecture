Add-Type -AssemblyName System.Drawing
$bitmap = New-Object System.Drawing.Bitmap(800, 1440)
$g = [System.Drawing.Graphics]::FromImage($bitmap)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::White)
$fonts = New-Object System.Drawing.Text.PrivateFontCollection
$fonts.AddFontFile('C:\Windows\Fonts\malgun.ttf')
$family = $fonts.Families[0]
$title = New-Object System.Drawing.Font($family, 28, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$heading = New-Object System.Drawing.Font($family, 23, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$body = New-Object System.Drawing.Font($family, 21, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$small = New-Object System.Drawing.Font($family, 18, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$ink = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#16324F'))
$muted = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#53667A'))
$blue = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#EDF5FF'))
$green = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#EAF7EF'))
$red = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#FFF0EE'))
$border = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#B8CEE7'), 2)
$arrow = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#6385A8'), 3)
$arrow.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap(5, 6)
$center = New-Object System.Drawing.StringFormat
$center.Alignment = [System.Drawing.StringAlignment]::Center
$center.LineAlignment = [System.Drawing.StringAlignment]::Center
function Text($text, $font, $x, $y, $w, $h) {
    $g.DrawString($text, $font, $ink, [System.Drawing.RectangleF]::new($x, $y, $w, $h), $center)
}
function Box($text, $y, $h, $fill) {
    $rect = [System.Drawing.Rectangle]::new(55, $y, 690, $h)
    $g.FillRectangle($fill, $rect)
    $g.DrawRectangle($border, $rect)
    Text $text $body 68 ($y+3) 664 ($h-6)
}
function Arrow($y) { $g.DrawLine($arrow, 400, $y, 400, ($y+20)) }

Text 'main7.py | 캐시 장애와 세션 확인' $title 25 20 750 55
Text '캐시는 원본으로 대체 · 세션 확인 실패는 접근 거절' $small 25 79 750 35

Text '① history: 버전별 대화 이력 조회' $heading 35 133 730 42
Box '사용자 ID → SQLite 최신 ID로 캐시 버전 확인' 185 65 $blue
Arrow 254
Box '해당 버전 키로 Redis 캐시 조회' 280 65 $blue
Arrow 349
Box "HIT: 정상 캐시 → JSON 복원`nMISS 또는 형식 오류: SQLite 최근 6개 → 캐시 재저장`nBYPASS: Redis 읽기 실패 → SQLite 원본 사용" 375 120 $blue
Arrow 499
Box "대화 이력 출력 (과거 → 현재 순서)`n캐시 쓰기 실패도 원본 결과 반환: MISS_WRITE_FAILED" 525 85 $green

Text '② add: 원본 저장 후 이전 캐시 정리' $heading 35 640 730 42
Box "사용자 ID + 메시지 → SQLite에 질문·모의 응답 저장`n한 트랜잭션으로 커밋" 692 80 $blue
Arrow 776
Box "이전 캐시 삭제 시도 → 실패해도 원본 저장은 유지`n다음 조회는 새 버전 키 사용" 802 85 $green

Text '③ create / session: 세션 생성과 확인' $heading 35 921 730 42
Box 'create: 세션 ID 생성 → Redis에 저장 / TTL 300초' 975 65 $blue
Arrow 1044
Box 'session: 세션 ID로 Redis에서 사용자 확인' 1070 65 $blue
Arrow 1139
Box "정상 세션 → 사용자 이름 출력`n세션 없음·만료 또는 Redis 장애 → 접근 거절" 1165 90 $red

Text "캐시 TTL 60초 / 최근 6개 메시지 / 실제 LLM 호출 없음`nhistory·add는 사용자 ID로 실행하며 세션 검증과는 별도 경로`ninit: SQLite 초기화 / evict: 현재 버전 캐시 삭제" $small 35 1290 730 110
$bitmap.Save((Join-Path $PSScriptRoot 'main7.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bitmap.Dispose()
$title.Dispose()
$heading.Dispose()
$body.Dispose()
$small.Dispose()
$fonts.Dispose()
