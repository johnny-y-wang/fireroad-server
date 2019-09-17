"""Database models for FireRoad Analytics services."""

from django.db import models
from django.utils import timezone

class RequestCount(models.Model):
    """Keeps track of a single request."""

    path = models.CharField(max_length=50, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.CharField(max_length=150, null=True)
    is_authenticated = models.BooleanField(default=False)
    student_unique_id = models.CharField(max_length=50, null=True)
    student_semester = models.CharField(max_length=25, null=True)

    def __unicode__(self):
        return u"{} by {} at {}{}".format(
            self.path,
            self.user_agent,
            self.timestamp,
            " (logged in)" if self.is_authenticated else ""
        )

    @staticmethod
    def tabulate_requests(early_time,
                          interval=None,
                          attribute_func=None,
                          distinct_users=False):
        """Retrieves request counts from the given time to present,
        bucketed by the given interval.

        Args:
            early_time: A timezone.datetime object indicating the minimum time
                to retrieve requests for.
            interval: A timezone.timedelta object indicating the period of time
                spanned by each returned bucket. If None, counts all requests
                together and returns a single dictionary.
            attribute_func: A function taking a RequestCount and returning a
                value to tabulate for each bucket.
            distinct_users: If True, count only one request per unique user.

        Returns:
            A list of tuples (time, dict), where time is a timezone.datetime
            object indicating the start time of the bucket, and dict is a
            dictionary mapping values returned by attribute_func to their
            counts in the bucket.
        """
        now = timezone.now()
        buckets = []
        if interval:
            curr = early_time
            while curr < now:
                buckets.append((curr, {}))
                curr += interval
        else:
            buckets.append((early_time, {}))

        seen_users = set()
        recent_requests = RequestCount.objects.filter(timestamp__gte=early_time)
        for request in recent_requests.iterator():
            if distinct_users and (not request.student_unique_id or
                                   request.student_unique_id in seen_users):
                continue
            seen_users.add(request.student_unique_id)
            for time, bucket in buckets:
                if (request.timestamp >= time and
                        (not interval or request.timestamp < time + interval)):
                    value = attribute_func(request) if attribute_func else None
                    bucket[value] = bucket.get(value, 0) + 1
                    break

        if not interval:
            return buckets[0][1]
        return buckets
