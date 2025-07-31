<?php
require 'includes/functions.php';
if (!is_logged_in()) {
    header("Location: index.php");
    exit;
}
redirect_based_on_role();
?>
