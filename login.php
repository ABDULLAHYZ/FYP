<?php
require 'includes/db.php';
require 'includes/functions.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    $pass = $_POST['password'];

    $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
    $stmt->execute([$email]);
    $user = $stmt->fetch();

    if ($user && password_verify($pass, $user['password'])) {
        session_start();
        $_SESSION['user_id'] = $user['user_id'];
        $_SESSION['username'] = $user['name'];
        $_SESSION['role'] = $user['role'];
        $_SESSION['logged_in'] = true; // Add this line
         
        header("Location: index.php");
    } else {
        echo "<script>alert('Invalid credentials'); window.location.href = 'signin.html';</script>";
    }
}
?>