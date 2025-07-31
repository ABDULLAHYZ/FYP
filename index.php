<?php
session_start();

?>

<!DOCTYPE html>
<html>

<head>
    <link rel="stylesheet" type="text/css" href="styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
</head>

<body>
    <div class="container">
        <header>
            <nav>
                <a href="#home">HOME</a> |
                <a href="#menu">MENU</a> |
                <a href="#location">LOCATION</a> |
                <a href="#aboutus">ABOUT US</a> |
                <a href="#contactus">CONTACT US</a>

                <div class="nav-button">
                    <?php if (isset($_SESSION['user_id']) && !empty($_SESSION['user_id'])): ?>
                        <span>Welcome, <?= htmlspecialchars($_SESSION['username']) ?>!</span>
                        <button class="btn white-btn" onclick="logout()">Logout</button>
                    <?php else: ?>
                        <button class="btn white-btn" id="loginBtn" onclick="login()">Sign In</button>
                        <button class="btn" id="registerBtn" onclick="register()">Sign Up</button>
                    <?php endif; ?>
                </div>

                <div class="nav-menu-btn">
                    <i class="bx bx-menu" onclick="myMenuFunction()"></i>
                </div>
            </nav>
        </header>

        <section id="home">
            <img src="banner.png">
        </section>

        <section id="menu">
            <h2>About Items

 
            </h2>

            <!-- First Item -->
            <div class="item-container reverse">
                <div class="item-description">
                    <h3>Samosa</h3>
                    <p>A samosa is a fried South Asian and West Asian snack. It is a pastry with a savory filling that
                        mostly consists of vegetables like spiced
                        potatoes, onions, and peas, but can also include meat or fish, or even cheese. Its name
                        originates from the Persian word sambosag . It is made in
                        different shapes, including triangular, cone, or crescent, depending on the region.
                        Samosas are often accompanied by chutney, and have origins in medieval times or earlier.
                        Sweet versions are also made.</p>
                </div>
                <div class="item-image">
                    <img src="Samosa.jpg" alt="Samosa">
                </div>
            </div>

            <!-- Second Item -->
            <div class="item-container">
                <div class="item-image">
                    <img src="Pizza.jpg" alt="Pizza">
                </div>
                <div class="item-description">
                    <h3>Pizza</h3>
                    <p>Pizza is an Italian, specifically Neapolitan, dish typically consisting of a flat base of
                        leavened wheat-based dough topped with tomato, cheese, and other ingredients, baked at a high
                        temperature, traditionally in a wood-fired oven. <br>

                        The term pizza was first recorded in 997 AD, in a Latin manuscript from the southern Italian
                        town of Gaeta, in Lazio, on the border with Campania. Raffaele Esposito is often credited for
                        creating the modern pizza in Naples.In 2009, Neapolitan pizza was registered
                        with the European Union as a traditional speciality guaranteed dish.
                    </p>
                </div>
            </div>
        </section>

        <section id="location">
            <h2>Location</h2>
            <p>Sector I-8/1, Street # 2, Islamabad, Pakistan.</p>
        </section>

        <section id="contactus">
            <h2>Contact Us</h2>
            <p>Got questions? Want to place an order? Call us at +92 333-9846454 or email us at
                muhammadabdullah14127@gmail.com</p>
        </section>

        <!-- Dialogflow Chatbot - Only for logged-in users -->
        <?php if  (isset($_SESSION['user_id']) && !empty($_SESSION['user_id'])){ ?>
        <script src="https://www.gstatic.com/dialogflow-console/fast/messenger/bootstrap.js?v=1"></script>
        <df-messenger intent="WELCOME" chat-title="Ray-BoT" agent-id="0a2f5186-b503-41d6-826c-0dce3e2107e5"
            language-code="en">
        </df-messenger>
        <?php } else 
        {?> <div style="text-align: center; margin: 20px;">
    <button class="floating-btn" onclick="login()">Sign-in To Order</button>
    </div>

        <?php }
        
        ?>

        <script>
            function login() {
                window.location.href = "signin.html";
            }

            function register() {
                window.location.href = "signup.html";
            }

            function logout() {
                window.location.href = "logout.php";
            }
        </script>

    </div>
</body>

</html>