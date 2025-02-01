
        const answers = [
            "Paletta is a premium video footage library offering authentic, education-driven content sourced directly from leading colleges and universities worldwide. Our platform provides subject-specific and location-focused footage, enabling you to enhance your projects with high-quality visuals that truly stand out.",
            "Paletta is designed for educators, marketers, content creators, and anyone seeking unique, high-quality educational footage. Whether you’re working on academic presentations, marketing campaigns, or creative storytelling, our library caters to your needs.",
            "Our collection includes a wide range of content, from subject-specific academic scenes to iconic university locations across the UK. We focus on authentic, education-driven visuals that highlight learning environments, student interactions, research activities, and more.",
            "You can browse our library and add your selected clips to your cart. After completing the checkout process, you’ll receive a download link to access your footage.",
            "All footage on Paletta is available in high-resolution formats, typically 4K or Full HD, ensuring top-notch quality for your projects.",
            "Paletta footage comes with flexible licensing options designed to meet a variety of project needs. You can review the specific licensing terms during the purchase process to ensure compliance with your intended use.",
            "Yes, Paletta offers the option to commission custom footage. If you require specific content that isn’t currently available in our library, get in touch with our team, and we’ll work with our network of educational partners to meet your needs.",
            "Yes, we offer subscription plans for users who require frequent access to our library. Subscriptions provide significant savings and exclusive benefits. Contact us to learn more about our plans.",
            "Absolutely! All clips come with watermarked previews so you can review the content and ensure it fits your project before making a purchase.",
            "If you have questions or need assistance, our team is here to help. You can reach us via email at support@paletta.com or through our contact form on the website.",
            "While we specialize in UK-based educational content, our library also features footage from leading global institutions. Use our search filters to explore a diverse range of locations.",
            "We are constantly adding new footage to our library, ensuring fresh and relevant content is always available. Sign up for our newsletter to stay updated on new arrivals and exclusive releases."
        ];

        function selectQuestion(element, index) {
            document.querySelectorAll('.faq-questions li').forEach(li => li.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('faq-answer').innerHTML = `<p>${answers[index]}</p>`;
        }

        function contactUs() {
            alert('Redirecting to the Contact Us page.');
        }
    