<?php
header('Content-Type: text/plain');

$host = getenv('MYSQL_HOST') ?: 'mysql';
$user = getenv('MYSQL_USER') ?: 'user';
$pass = getenv('MYSQL_PASSWORD') ?: 'password';
$db   = getenv('MYSQL_DATABASE') ?: 'database';
$url  = getenv('SUBSCRIPTION_BASE_URL') ?: 'https://raw.githubusercontent.com/VerkholantsevDanila/IO/refs/heads/main/keys';

$mysqli = new mysqli($host, $user, $pass, $db);

if ($mysqli->connect_error) {
    http_response_code(500);
    die("Error: Database connection unsuccessful: " . $mysqli->connect_error);
}

$token = $_GET['token'] ?? null;

if (!$token) {
    http_response_code(400);
    die("Error: Token not provided.");
}

if (!preg_match('/^[a-zA-Z0-9]{24}$/', $token)) {
    http_response_code(400);
    die("Error: Token invalid.");
}

$query = "SELECT tok.token, tar.region, tok.end_date FROM tokens tok JOIN tariffs tar ON tok.tariff_id = tar.id WHERE tok.token = ?";
$stmt = $mysqli->prepare($query);

if (!$stmt) {
    http_response_code(500);
    die("Error: Query preparation error: " . $mysqli->error);
}

$stmt->bind_param("s", $token);
$stmt->execute();

$stmt->bind_result($usertoken, $region, $endDate);

if ($stmt->fetch()) {
    http_response_code(200);
    $profiletitle = "🔹IOConnect🔹".$region."🔹";
    $profiletitle_b64 = base64_encode($profiletitle);
    header('Content-Type: text/plain');
    echo "//profile-title: base64:".$profiletitle_b64."\n";
    echo "//profile-update-interval: 8\n";
    echo "//subscription-userinfo: upload=0; download=0; total=10737418240000000; expire=".$endDate."\n";
    echo "//support-url: https://t.me/ioioconnectbot\n";
    echo "//profile-web-page-url: https://t.me/ioioconnectbot\n";
    echo "//user-token: ".$usertoken."\n\n";

$userurl = $url."/".$region.".txt";
$content = file_get_contents($userurl);
echo $content;

} else {
    http_response_code(200);
    $profiletitle = "🔹IOConnect🔹";
    $profiletitle_b64 = base64_encode($profiletitle);
    header('Content-Type: text/plain');
    echo "//profile-title: base64:".$profiletitle_b64."\n";
    echo "//profile-update-interval: 24\n";
    echo "//subscription-userinfo: upload=1024; download=1024; total=1024; expire=".time()."\n";
    echo "//support-url: https://t.me/ioioconnectbot\n";
    echo "//profile-web-page-url: https://t.me/ioioconnectbot\n";
    echo "//user-token: ".$token."\n\n";
    echo "ss://none:0000@127.0.0.1:1#%F0%9F%94%B4%20EXPIRED%20%F0%9F%94%B4\n";
}

$stmt->close();
$mysqli->close();
?>
