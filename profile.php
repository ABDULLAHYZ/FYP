<?php
require 'includes/functions.php';
require 'includes/db.php';

if (!is_logged_in()) {
    header("Location: index.php");
    exit;
}
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_SESSION['user_id']]);
$user = $stmt->fetch();
?>
<form method="POST">
  Username: <input type="text" name="username" value="<?= $user['username'] ?>"><br>
  Email: <input type="email" name="email" value="<?= $user['email'] ?>"><br>
  <input type="submit" value="Update">
</form>
<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $stmt = $pdo->prepare("UPDATE users SET username = ?, email = ? WHERE id = ?");
    $stmt->execute([$_POST['username'], $_POST['email'], $_SESSION['user_id']]);
    echo "Updated successfully!";
}
?>
