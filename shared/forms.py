from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE
from .models import UserProfile, Page


class FlowbiteFormMixin:
    input_class = (
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
        "focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
        "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
        "dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
    )

    file_input_class = (
        "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg "
        "cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none "
        "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
    )

    checkbox_class = "w-5 h-5 border border-default-medium rounded bg-neutral-secondary-medium focus:ring-2 focus:ring-brand-soft"
    radio_class = "w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget
            classes = widget.attrs.get("class", "")

            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs["class"] = f"{classes} {self.checkbox_class}".strip()
            elif isinstance(widget, (forms.RadioSelect,)):
                widget.attrs["class"] = f"{classes} {self.radio_class}".strip()
            elif isinstance(widget, (forms.FileInput,)):
                widget.attrs["class"] = f"{classes} {self.file_input_class}".strip()
            else:
                widget.attrs["class"] = f"{classes} {self.input_class}".strip()

            widget.attrs.setdefault("id", f"id_{name}")


class LoginForm(FlowbiteFormMixin, AuthenticationForm):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Your username"),
                "autocomplete": "username",
            }
        ),
        error_messages={
            "required": _("Please enter your username."),
        },
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "placeholder": _("Your password"),
                "autocomplete": "current-password",
            }
        ),
        error_messages={
            "required": _("Please enter your password."),
        },
    )


class RegisterForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]
        labels = {
            "username": _("Username"),
            "email": _("Email address"),
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": _("Choose a username"),
                    "autocomplete": "username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": _("name@example.com"),
                    "autocomplete": "email",
                }
            ),
        }
        help_texts = {
            "username": _("Letters, digits and @/./+/-/_ only."),
        }
        error_messages = {
            "username": {
                "required": _("Username is required."),
                "unique": _("This username is already taken."),
            },
            "email": {
                "required": _("Email is required."),
                "invalid": _("Enter a valid email address."),
            },
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        # Password will be set in the view
        if commit:
            user.save()
            # UserProfile is already created by signal 'ensure_profile_exists' in models.py
            # But we can update it here if needed.
        return user


class FlowbitePasswordResetForm(FlowbiteFormMixin, PasswordResetForm):
    pass


class FlowbiteSetPasswordForm(FlowbiteFormMixin, SetPasswordForm):
    pass


class FlowbitePasswordChangeForm(FlowbiteFormMixin, PasswordChangeForm):
    pass


class ProfileUpdateForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "email": _("Email"),
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": _("Your first name"),
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": _("Your last name"),
                    "autocomplete": "family-name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": _("name@example.com"),
                    "autocomplete": "email",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("This email is already in use."))
        return email


class PageForm(FlowbiteFormMixin, forms.ModelForm):
    title_en = forms.CharField(
        label=_("Title (English)"),
        max_length=255,
        required=True,
    )
    title_fr = forms.CharField(
        label=_("Title (French)"),
        max_length=255,
        required=True,
    )
    content_en = forms.CharField(
        label=_("Content (English)"),
        required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
    )
    content_fr = forms.CharField(
        label=_("Content (French)"),
        required=True,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
    )
    slug_en = forms.SlugField(
        label=_("Slug (English)"),
        required=True,
    )
    slug_fr = forms.SlugField(
        label=_("Slug (French)"),
        required=True,
    )

    class Meta:
        model = Page
        fields = [
            "title_en",
            "title_fr",
            "slug_en",
            "slug_fr",
            "content_en",
            "content_fr",
            "is_active",
        ]
        widgets = {
            "is_active": forms.CheckboxInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Basic required fields validation is handled by field-level required=True
        return cleaned_data
