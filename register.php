<?php
require 'includes/db.php';

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $username = $_POST['username'];
    $email    = $_POST['email'];
    $number    = $_POST['phonenumber'];
    $password = password_hash($_POST['password'], PASSWORD_DEFAULT);

    // Check if user already exists
    $check = $pdo->prepare("SELECT * FROM users WHERE email = ?");
    $check->execute([$email]);

    if ($check->fetch()) {
        echo "<script>alert('Email already exists!'); window.location.href='signup.html';</script>";
        exit;
    }

    // Insert new user
    $stmt = $pdo->prepare("INSERT INTO users (name, email,phone, password) VALUES (?, ?, ?,?)");
    $stmt->execute([$username, $email,$number, $password]);

    echo "<script>alert('Registration successful! Please sign in.'); window.location.href='signin.html';</script>";
}
?>
