from celery_app.celery import celery_app as celery
from random import choice


@celery.task
def add(x, y):
    return x + y
#
#
# @cel_app.task
# def mul(x, y):
#     return x * y
#
#
# @cel_app.task
# def xsum(numbers):
#     return sum(numbers)


@celery.task
def calculate(r):
    for i in range(r):
        data = "".join(choice("ABCDE" + f"{((i ** i) ** (i ** i)) ** i}") for i in range(0))
    return "Done"
