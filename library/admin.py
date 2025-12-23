from django.contrib import admin

from library.models import Payment, Book, Borrowing, Author

admin.site.register(Payment)
admin.site.register(Book)
admin.site.register(Borrowing)
admin.site.register(Author)
