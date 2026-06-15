from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from .models import User, Product, Review, ProducerProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Seu usuário'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Sua senha'})
    )


class RegisterForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('consumer', '🛒 Consumidor — Quero comprar produtos fresquinhos'),
        ('producer', '🌾 Produtor — Quero vender meus produtos da fazenda'),
    ]

    first_name = forms.CharField(
        label='Nome', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Seu nome'})
    )
    last_name = forms.CharField(
        label='Sobrenome', max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Seu sobrenome'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control farm-input', 'placeholder': 'seu@email.com'})
    )
    phone = forms.CharField(
        label='Telefone', max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': '(00) 00000-0000'})
    )
    city = forms.CharField(
        label='Cidade', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Sua cidade'})
    )
    user_type = forms.ChoiceField(
        label='Tipo de cadastro', choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'farm-radio'})
    )
    photo = forms.ImageField(
        label='Foto de perfil', required=False,
        widget=forms.FileInput(attrs={'class': 'form-control farm-input'})
    )
    farm_name = forms.CharField(
        label='Nome da fazenda', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Nome da sua fazenda'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'city',
                  'user_type', 'photo', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control farm-input', 'placeholder': 'Escolha um usuário'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control farm-input', 'placeholder': 'Crie uma senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control farm-input', 'placeholder': 'Confirme a senha'})
        self.fields['username'].label = 'Usuário'
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmar senha'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.city = self.cleaned_data['city']
        user.user_type = self.cleaned_data['user_type']
        if self.cleaned_data.get('photo'):
            user.photo = self.cleaned_data['photo']
        if commit:
            user.save()
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'weight',
                  'stock', 'is_available', 'is_featured', 'is_promotion', 'promotion_price', 'photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Nome do produto'}),
            'category': forms.Select(attrs={'class': 'form-select farm-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control farm-input', 'rows': 3, 'placeholder': 'Descreva seu produto...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control farm-input', 'step': '0.01', 'min': '0'}),
            'weight': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Ex: 500g, 1kg'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control farm-input', 'min': '0'}),
            'promotion_price': forms.NumberInput(attrs={'class': 'form-control farm-input', 'step': '0.01', 'min': '0'}),
            'photo': forms.FileInput(attrs={'class': 'form-control farm-input'}),
        }
        labels = {
            'name': 'Nome do produto',
            'description': 'Descrição',
            'price': 'Preço (R$)',
            'weight': 'Peso/Unidade',
            'stock': 'Estoque',
            'is_available': 'Disponível para venda',
            'is_featured': 'Produto em destaque',
            'is_promotion': 'Em promoção',
            'promotion_price': 'Preço promocional (R$)',
            'photo': 'Foto do produto',
        }


class ReviewForm(forms.ModelForm):
    STAR_CHOICES = [(i, '⭐' * i) for i in range(1, 6)]

    class Meta:
        model = Review
        fields = ['quality', 'delivery', 'service', 'comment']
        widgets = {
            'quality': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)],
                                    attrs={'class': 'form-select farm-input'}),
            'delivery': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)],
                                     attrs={'class': 'form-select farm-input'}),
            'service': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)],
                                    attrs={'class': 'form-select farm-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control farm-input', 'rows': 3,
                                             'placeholder': 'Conte como foi sua experiência...'}),
        }
        labels = {
            'quality': 'Qualidade do produto',
            'delivery': 'Entrega',
            'service': 'Atendimento',
            'comment': 'Comentário',
        }


class ConsumerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'city', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Seu nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Seu sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control farm-input', 'placeholder': 'seu@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': '(00) 00000-0000'}),
            'city': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Sua cidade'}),
            'photo': forms.FileInput(attrs={'class': 'form-control farm-input'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'phone': 'Telefone',
            'city': 'Cidade',
            'photo': 'Foto de perfil',
        }


class FarmSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control farm-input'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control farm-input'})
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password2'].label = 'Confirmar nova senha'


class ProducerProfileForm(forms.ModelForm):
    class Meta:
        model = ProducerProfile
        fields = ['farm_name', 'description', 'address', 'city', 'state', 'cover_photo']
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Nome da fazenda'}),
            'description': forms.Textarea(attrs={'class': 'form-control farm-input', 'rows': 4,
                                                 'placeholder': 'Conte sobre sua fazenda e produção...'}),
            'address': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Endereço'}),
            'city': forms.TextInput(attrs={'class': 'form-control farm-input', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'form-control farm-input', 'maxlength': '2', 'placeholder': 'UF'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control farm-input'}),
        }
        labels = {
            'farm_name': 'Nome da fazenda',
            'description': 'Sobre a fazenda',
            'address': 'Endereço',
            'city': 'Cidade',
            'state': 'Estado (UF)',
            'cover_photo': 'Foto da fazenda',
        }
