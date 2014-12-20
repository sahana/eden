# What does this Dockerfile do?
This Dockerfile has all the dependencies needed to run Sahana Eden for developing and demos.

1. You can try out Sahana Eden by running the following - Sahana Eden will be running on http://localhost:8000/eden/

	```
	docker run -p 8000:8000 sahana/eden
	```

2. You can develop with this dockerfile by running the following - this shares your eden directory with the container. Replace <path_to_eden_repo> with the path to your local eden repo.

	```
	docker run -v <path_to_eden_repo>:/home/web2py/	application/eden -p 8000:8000 sahana/eden
	```

# Building the Dockerfile

You can build the dockerfile by running the following from inside the eden directory.

```
docker build -t sahana/eden .
```

**NOTE:** This Dockerfile runs the web2py development webserver. Production deployments will need to modify this Dockerfile with relevant nginx and uwsgi additions.
 
