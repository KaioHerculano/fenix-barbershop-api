from django.db.models import Sum
from django.shortcuts import get_object_or_404

from company.models import Company
from loyalty.models import LoyaltyCard, LoyaltyTransaction


def get_active_company_by_slug(company_slug):
    return get_object_or_404(Company, slug=company_slug, is_active=True)


def get_user_loyalty_cards(user, company_slug=None):
    queryset = LoyaltyCard.objects.filter(user=user).select_related("company")
    if company_slug:
        get_active_company_by_slug(company_slug)
        queryset = queryset.filter(company__slug=company_slug, company__is_active=True)
    return queryset.order_by("company__name")


def get_user_loyalty_summary(user, company_slug=None):
    cards = list(get_user_loyalty_cards(user, company_slug))
    if company_slug and not cards:
        company = get_active_company_by_slug(company_slug)
        cards = [
            LoyaltyCard(
                company=company,
                user=user,
                points_balance=0,
            )
        ]
    return {
        "total_points_balance": sum(card.points_balance for card in cards),
        "cards": cards,
    }


def get_user_loyalty_transactions(user, company_slug=None):
    queryset = LoyaltyTransaction.objects.filter(user=user).select_related(
        "company",
        "appointment",
        "appointment__service",
    )
    if company_slug:
        get_active_company_by_slug(company_slug)
        queryset = queryset.filter(company__slug=company_slug, company__is_active=True)
    return queryset.order_by("-created_at")


def get_user_points_totals(user, company_slug=None):
    queryset = LoyaltyTransaction.objects.filter(user=user)
    if company_slug:
        get_active_company_by_slug(company_slug)
        queryset = queryset.filter(company__slug=company_slug, company__is_active=True)
    return {
        "earned_points": queryset.filter(type=LoyaltyTransaction.Type.EARN).aggregate(
            total=Sum("points")
        )["total"]
        or 0,
        "redeemed_points": queryset.filter(
            type=LoyaltyTransaction.Type.REDEEM
        ).aggregate(total=Sum("points"))["total"]
        or 0,
        "adjustment_points": queryset.filter(
            type=LoyaltyTransaction.Type.ADJUSTMENT
        ).aggregate(total=Sum("points"))["total"]
        or 0,
    }
