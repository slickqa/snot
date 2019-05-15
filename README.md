Snot: A nose Plugin
===================

Snot is a nose plugin that will allow results from python unit tests to report to Slick.

OPTIONS:

--slick-url
    the base url of the slick web app [SLICK_URL]
--slick-project-name
    the name of the project in slick to use [SLICK_PROJECT_NAME]
--slick-release
    the release under which to file the results in slick [SLICK_RELEASE]
--slick-build
    the build under which to file the results in slick [SLICK_BUILD]
--slick-build-from-function
    get the slick build from a function.  The parameter should be the module and function name to call [SLICK_BUILD_FROM_FUNCTION].
--slick-testplan
    the testplan under which to file the results in slick [SLICK_TESTPLAN]
--slick-testrun-name
    the name of the testrun to create in slick [SLICK_TESTRUN_NAME]
--slick-environment-name
    the name of the environment in slick to use in the testrun [SLICK_ENVIRONMENT_NAME]
--slick-testrun-group
    the name of the testrun group in slick to add this testrun to (optional) [SLICK_ENVIRONMENT_NAME]
--slick-agent-name
    what to put in slick's hostname field in the result.
--slick-schedule-results
    Schedule empty results in slick, but do not run the tests
--slick-schedule-add-requirement
    Add a requirement to all results when scheduling.
--slick-schedule-add-attribute
    Add an attribute to all results when scheduling.
--slick-schedule-new-requires
    apply the requires directly on the result as an attribute.
--slick-testrun-id
    Instead of creating a new testrun, use an existing one.
--slick-result-id
    Instead of creating a new result in the testrun, update an existing one.
--snot-no-log-capture
    Don't capture the logs from the logging framework
--slick-organize-by-tag
    A space delimited list of tag keys to base test run names after. Will be " - " delimited.
--slick-sequential-testrun
    Use with slick-schedule-results; schedules an entire testrun to be ran in sequence rather than distributed.

