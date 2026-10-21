from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render

from reviews.models import Review
from users.models import Profile
from .forms import PropertyForm, PropertyImageUploadForm, PropertySearchForm
from .models import Property, PropertyImage


def home(request):
    listings = Property.objects.select_related("host").prefetch_related("images").annotate(rating=Avg("reviews__rating"))
    search_form = PropertySearchForm(request.GET or None)
    filters = {
        "location": request.GET.get("location", ""),
        "type": request.GET.get("type", ""),
        "min_price": request.GET.get("min_price", ""),
        "max_price": request.GET.get("max_price", ""),
    }
    if search_form.is_valid():
        cleaned = search_form.cleaned_data
        if cleaned["location"]:
            listings = listings.filter(location__icontains=cleaned["location"].strip())
        if cleaned["type"]:
            listings = listings.filter(property_type=cleaned["type"])
        if cleaned["min_price"] is not None:
            listings = listings.filter(price_per_night__gte=cleaned["min_price"])
        if cleaned["max_price"] is not None:
            listings = listings.filter(price_per_night__lte=cleaned["max_price"])
    return render(request, "properties/home.html", {
        "listings": listings,
        "types": Property.TYPE_CHOICES,
        "filters": filters,
        "search_form": search_form,
    })


def detail(request, pk):
    listing = get_object_or_404(
        Property.objects.select_related("host", "host__profile").prefetch_related("images", "reviews__guest"),
        pk=pk,
    )
    can_review = False
    if request.user.is_authenticated:
        from bookings.models import Booking
        from django.utils import timezone
        can_review = Booking.objects.filter(
            property=listing,
            guest=request.user,
            check_out__lte=timezone.localdate(),
            status=Booking.CONFIRMED,
        ).exists() and not Review.objects.filter(property=listing, guest=request.user).exists()
    return render(request, "properties/detail.html", {"property": listing, "can_review": can_review})


def _host_required(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.role != Profile.HOST:
        raise PermissionDenied("Only host accounts can manage property listings.")


@login_required
def create(request):
    _host_required(request)
    form = PropertyForm(request.POST or None)
    image_form = PropertyImageUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid() and image_form.is_valid():
        listing = form.save(commit=False)
        listing.host = request.user
        listing.save()
        for image in image_form.cleaned_data["images"]:
            PropertyImage.objects.create(property=listing, image=image)
        messages.success(request, "Your place is live.")
        return redirect(listing.get_absolute_url())
    return render(request, "properties/property_form.html", {"form": form, "image_form": image_form, "heading": "Make room for a good story"})


@login_required
def edit(request, pk):
    listing = get_object_or_404(Property, pk=pk)
    if listing.host_id != request.user.id:
        raise PermissionDenied
    form = PropertyForm(request.POST or None, instance=listing)
    image_form = PropertyImageUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid() and image_form.is_valid():
        form.save()
        for image in listing.images.filter(pk__in=request.POST.getlist("delete_images")):
            image.delete()
        for image in image_form.cleaned_data["images"]:
            PropertyImage.objects.create(property=listing, image=image)
        messages.success(request, "Your listing has been updated.")
        return redirect(listing.get_absolute_url())
    return render(request, "properties/property_form.html", {"form": form, "image_form": image_form, "property": listing, "heading": "A little refresh"})


@login_required
def delete(request, pk):
    listing = get_object_or_404(Property, pk=pk)
    if listing.host_id != request.user.id:
        raise PermissionDenied
    if request.method == "POST":
        listing.delete()
        messages.success(request, "Your listing has been removed.")
        return redirect("users:dashboard")
    return render(request, "properties/property_confirm_delete.html", {"property": listing})
