from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property
from .forms import BookingForm
from .models import Booking


@login_required
def create(request, property_id):
    listing = get_object_or_404(Property, pk=property_id)
    form = BookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        dates = form.cleaned_data
        overlaps = Booking.objects.filter(property=listing).exclude(status=Booking.CANCELLED).filter(
            check_in__lt=dates["check_out"], check_out__gt=dates["check_in"]
        ).exists()
        if overlaps:
            form.add_error(None, "Those dates are no longer available. Try another stay.")
        elif listing.host_id == request.user.id:
            form.add_error(None, "You can’t book your own place.")
        else:
            nights = (dates["check_out"] - dates["check_in"]).days
            booking = Booking.objects.create(
                property=listing,
                guest=request.user,
                check_in=dates["check_in"],
                check_out=dates["check_out"],
                guests=dates["guests"],
                total_price=listing.price_per_night * Decimal(nights),
            )
            messages.success(request, "Your booking request has been sent.")
            return redirect("users:dashboard")
    return render(request, "bookings/booking_form.html", {"form": form, "property": listing})


@login_required
@require_POST
def cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user.id not in (booking.guest_id, booking.property.host_id):
        raise PermissionDenied
    if booking.status != Booking.CANCELLED:
        booking.status = Booking.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "The booking has been cancelled.")
    return redirect("users:dashboard")


@login_required
@require_POST
def update_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk, property__host=request.user)
    status = request.POST.get("status")
    if booking.status != Booking.CANCELLED and status in (Booking.CONFIRMED, Booking.CANCELLED):
        booking.status = status
        booking.save(update_fields=["status"])
        messages.success(request, f"Booking {status}.")
    return redirect("users:dashboard")
