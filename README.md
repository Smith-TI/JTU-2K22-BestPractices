# Instructions
This assignment consists of a django-rest-framework app that has several violations of common best practices.
The assignment is mostly open-ended, just like the definition of what exactly is a best practice and what's not 😉

Fork this repository and make a new branch named jtu-2k22-<ad_username>, fix as many best practices violations as you can find and make a PR, and assign kushal-ti as the reviewer.

If you don't know anything about django-rest-framework don't worry. You don't have to run the project or make any changes that requires knowledge intimate knowledge of django-rest-framework

# Setup Instructions

1. Clone the repo and `cd` into it.
2. Run `cp cjapp/.env.sample cjapp/.env` and fill all the fields in it.
3. Run `python manage.py migrate` to run any missing migrations to the db
3. Build and run the Docker Container