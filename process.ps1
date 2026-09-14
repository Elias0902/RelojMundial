Add-Type -AssemblyName System.Drawing

$src_dir = 'C:\Users\Personal\.gemini\antigravity\brain\553e80d4-2ff2-4f65-bb3b-1288444f1762'
$dst_dir = 'c:\Users\Personal\Downloads\GIT\RelojMundial\assets'

$orig_img = 'C:\Users\Personal\.gemini\antigravity\brain\553e80d4-2ff2-4f65-bb3b-1288444f1762\.user_uploaded\media_1789366202347.jpg'
$work_img = (Get-ChildItem -Path $src_dir -Filter 'avatar_work*.jpg')[0].FullName
$lunch_img = (Get-ChildItem -Path $src_dir -Filter 'avatar_lunch*.jpg')[0].FullName
$preclose_img = (Get-ChildItem -Path $src_dir -Filter 'avatar_preclose*.jpg')[0].FullName
$rest_img = (Get-ChildItem -Path $src_dir -Filter 'avatar_rest*.jpg')[0].FullName

$images = @{
    'avatar_count.png' = $orig_img
    'avatar_work.png' = $work_img
    'avatar_lunch.png' = $lunch_img
    'avatar_preclose.png' = $preclose_img
    'avatar_rest.png' = $rest_img
}

foreach ($kv in $images.GetEnumerator()) {
    Write-Host "Processing $($kv.Key) from $($kv.Value)..."
    $img = [System.Drawing.Image]::FromFile($kv.Value)
    
    # Check if we can make it transparent by replacing white
    $bmp = new-object System.Drawing.Bitmap($img)
    $bmp.MakeTransparent([System.Drawing.Color]::White)
    
    # Resize to max 300x300
    $scale = 300.0 / $bmp.Width
    if ($bmp.Height * $scale -gt 300) {
        $scale = 300.0 / $bmp.Height
    }
    $newWidth = [math]::Floor($bmp.Width * $scale)
    $newHeight = [math]::Floor($bmp.Height * $scale)
    
    $resized = new-object System.Drawing.Bitmap($newWidth, $newHeight)
    $g = [System.Drawing.Graphics]::FromImage($resized)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($bmp, 0, 0, $newWidth, $newHeight)
    $g.Dispose()
    
    $out_path = Join-Path $dst_dir $kv.Key
    $resized.Save($out_path, [System.Drawing.Imaging.ImageFormat]::Png)
    
    $img.Dispose()
    $bmp.Dispose()
    $resized.Dispose()
    Write-Host "Saved $out_path"
}
Write-Host "Done!"
