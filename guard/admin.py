from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import GuardUser
from django.contrib.auth.models import Group
from django import forms


class GuardUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)

    class Meta:
        model = GuardUser
        # email is REQUIRED on the model (unique=True, no null/blank)
        fields = ('username', 'email', 'is_staff', 'is_active')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Passwords don't match"))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # No manual save_m2m() here; allow ModelAdmin to handle it via the standard flow
        return user


class GuardUserChangeForm(forms.ModelForm):
    class Meta:
        model = GuardUser
        fields = ('username', 'email', 'is_staff', 'is_active', 'is_verified', 'groups', 'user_permissions')


# Guard against double-unregister
if admin.site.is_registered(Group):
    admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(GuardUser)
class GuardUserAdmin(admin.ModelAdmin):
    add_form    = GuardUserCreationForm
    form        = GuardUserChangeForm

    list_display  = ['username', 'email', 'is_staff', 'is_active', 'is_verified']
    list_filter   = ['is_staff', 'is_active', 'is_verified']
    search_fields = ['username', 'email']
    ordering      = ['email']

    filter_horizontal = ('groups', 'user_permissions')

    # Fieldsets for the EDIT view
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_verified', 'groups', 'user_permissions')}),
    )

    # Fieldsets for the ADD view
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Return the creation form when adding, change form when editing."""
        if obj is None:
            kwargs['form'] = self.add_form
        else:
            kwargs['form'] = self.form
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.fieldsets


GuardUser._meta.verbose_name = _("User")
GuardUser._meta.verbose_name_plural = _("Users")