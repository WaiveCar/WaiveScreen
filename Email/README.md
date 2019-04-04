The email templates have a format:

For each template:
  * The first line is the subject
  * Include contents of `_header`
  * Include the body of the message
  * Include contents of `_footer`

This is important to include both. If you note the contents of `_header` and `_footer` you'll see that they aren't well formed HTML. 

The variable system used is {{ variable }} which is compatible with python's Jinja, PHP's twig and probably many other systems.
