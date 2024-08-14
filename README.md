# gitlab-ci-env

Python script/module that generates the GitLab CI predefined env variables `CI_COMMIT_REF_SLUG` and `CI_ENVIRONMENT_SLUG` given a branch name and environment name.

```
$ python3 gitlab-ci-env.py --branch review/TEST-branch-with-really-long-name --environment-name 'deployment-$CI_COMMIT_REF_NAME'
{
  "CI_COMMIT_REF_NAME": "review/TEST-branch-with-really-long-name",
  "CI_COMMIT_REF_SLUG": "review-test-branch-with-really-long-name",
  "CI_ENVIRONMENT_NAME": "deployment-review/TEST-branch-with-really-long-name",
  "CI_ENVIRONMENT_SLUG": "deployment-revie-l58kaf"
}
```

You can also copy this module into your codebase and use the individual functions or the `PredefinedVariables` class. Do whatever you want. It's unlicensed.

## Reason

Documentation on how the `CI_COMMIT_REF_SLUG` and `CI_ENVIRONMENT_SLUG` env variables are generated is not very comprehensive, and there's no GitLab API that gives you these values for a pipeline.

Since these are often used to generate URLs for test deployments, this can lead to huge pains when you need to know these URLs ahead of time to orchestrate other deployments. Many hours of my life were wasted waiting for jobs to run just so that I could get the value of these env variables and run the jobs again, this time with the correct env variables set. Believe me, being able to know these values ahead of time saves a ton of man-hours.
