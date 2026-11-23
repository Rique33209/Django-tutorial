from django.db.models import F
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from pathlib import Path
import pandas as pd
from .models import Question

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
         Return the last five published questions (not including those set to be published in the future).
         """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

class DetailView(generic.DetailView):
    ...

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())
    model = Question
    template_name = "polls/detail.html"

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"
# ...
def index(request):
    latest_question_list = Question.objects.order_by("-pub_date")[:5]
    template = loader.get_template("index.html")
    context = {"latest_question_list": latest_question_list}
    return HttpResponse(template.render(context, request))

def details(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, "polls/details.html", {"question": question})

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})

def vote(request, question_id):
    # same as above, no changes needed.
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except Exception as e:#(KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
         return render(request,
        "polls/details.html" ,
        {
            "question": question,
            "error_message": "You didn't selet a choice.",
        },
    )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after succesfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

def fruit_data(request):
    file_path = Path(__file__).resolve().parent / "fruit_size_data.xlsx"

    df = pd.read_excel(file_path)

    # Remove empty columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    #Get selected header_id from URL
    selected_header = request.GET.get("header_id")

    if selected_header:
        df = df[df["header_id"] == int(selected_header)]

    average_estimated_size = round(
        df["size_in_mm_estimate"].mean(), 2
    )

    min_reading = df["size_in_mm_actual"].min()
    max_reading = df["size_in_mm_actual"].max()

    header_ids = sorted(df["header_id"].unique())

    size_distribution = (
        df.groupby("size_count")
        .size()
        .reset_index(name="frequency")
        .to_dict("records")
    )

    labels = [str(item["size_count"]) for item in size_distribution]
    values = [item["frequency"] for item in size_distribution]

    data = df.to_dict("records")

    return render(
        request,
        "polls/fruit_data.html",
        {
            "data": data,
            "columns": df.columns,
            "average_estimated_size": average_estimated_size,
            "header_ids": header_ids,
            "selected_header": selected_header,
            "min_reading": min_reading,
            "max_reading": max_reading,
            "size_distribution": size_distribution,
            "labels": labels,
            "values": values,
        },
    )