(function(angular) {

  'use strict';

  angular.module('boac').controller('StudentController', function(
    authService,
    boxplotService,
    googleAnalyticsService,
    studentFactory,
    watchlistFactory,
    $base64,
    $location,
    $scope,
    $stateParams
  ) {

    $scope.student = {
      canvasProfile: null,
      enrollmentTerms: null,
      isLoading: true
    };

    $scope.showAllTerms = false;
    $scope.showDismissedAlerts = false;

    $scope.dismissAlert = function(alertId) {
      studentFactory.dismissAlert(alertId).then(function() {
        var dismissed = _.remove($scope.alerts.shown, {id: alertId});
        Array.prototype.push.apply($scope.alerts.dismissed, dismissed);
      }).catch(function(error) {
        if (error.data) {
          $scope.error = _.truncate(error.data.message, {length: 200}) || 'An unexpected server error occurred.';
        } else {
          throw error;
        }
      });
    };

    var loadStudent = function(uid) {
      $scope.student.isLoading = true;
      studentFactory.analyticsPerUser(uid).then(function(analytics) {
        $scope.student = analytics.data;
        // Track view event
        var preferredName = $scope.student.sisProfile && $scope.student.sisProfile.preferredName;
        googleAnalyticsService.track('student', 'view-profile', preferredName, parseInt(uid, 10));
      }).catch(function(error) {
        $scope.error = _.truncate(error.data.message, {length: 200}) || 'An unexpected server error occurred.';
      }).then(function() {
        var athleticsProfile = $scope.student.athleticsProfile;
        if (athleticsProfile) {
          athleticsProfile.fullName = athleticsProfile.firstName + ' ' + athleticsProfile.lastName;
          if (athleticsProfile.sid) {
            studentFactory.getAlerts(athleticsProfile.sid).then(function(alerts) {
              $scope.alerts = alerts.data;
            });
          }
        }
        $scope.student.isLoading = false;
      });
    };

    var prepareReturnUrl = function(uid) {
      var encodedReturnUrl = $location.search().r;
      if (!_.isEmpty(encodedReturnUrl)) {
        $location.search('r', null).replace();
        var url = $base64.decode(decodeURIComponent(encodedReturnUrl));
        var separator = _.includes(url, '?') ? '&' : '?';
        $scope.returnUrl = url + separator + 'a=' + uid;
        $scope.hideFeedbackLink = true;
      }
    };

    var init = function() {
      var uid = $stateParams.uid;
      loadStudent(uid);
      prepareReturnUrl(uid);
      $scope.isWatchlistLoading = true;
      watchlistFactory.getMyWatchlist().then(function(response) {
        $scope.myWatchlist = response.data;
        $scope.isWatchlistLoading = false;
      });
    };

    $scope.drawBoxplot = function(termId, displayName, courseId, metric) {
      var term = _.find($scope.student.enrollmentTerms, {termId: termId});

      var courseSites;
      if (displayName === 'unmatchedCanvasSites') {
        courseSites = term.unmatchedCanvasSites;
      } else {
        var enrollment = _.find(term.enrollments, {displayName: displayName});
        courseSites = enrollment.canvasSites;
      }

      var course = _.find(courseSites, {canvasCourseId: courseId});
      var elementId = 'boxplot-' + courseId + '-' + metric;
      boxplotService.drawBoxplotStudent(elementId, course.analytics[metric]);
    };

    init();
  });

}(window.angular));
