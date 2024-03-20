<link rel="icon" href="https://blindllama.mithrilsecurity.io/en/latest/assets/logo.png">

<%!
    from pdoc.html_helpers import minify_css
%>
<%def name="homelink()" filter="minify_css">
    .homelink {
        display: block;
        font-size: 2em;
        font-weight: bold;
        padding-bottom: .5em;
        border-bottom: 1px solid silver;
    }
    .homelink:hover {
        color: f0ba2d;
    }
    .homelink img {
        max-width:20%;
        max-height: 5em;
        margin: auto;
        margin-bottom: .3em;
    }
</%def>

<style>${homelink()}</style>

<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id=%27+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-TVD93MF');</script>
<!-- End Google Tag Manager -->
