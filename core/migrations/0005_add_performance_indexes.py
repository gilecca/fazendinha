from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_seed_categories'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS idx_product_is_available  ON core_product (is_available);",
                "CREATE INDEX IF NOT EXISTS idx_product_is_featured    ON core_product (is_featured);",
                "CREATE INDEX IF NOT EXISTS idx_product_is_promotion   ON core_product (is_promotion);",
                "CREATE INDEX IF NOT EXISTS idx_order_status           ON core_order (status);",
                "CREATE INDEX IF NOT EXISTS idx_order_payment_status   ON core_order (payment_status);",
                "CREATE INDEX IF NOT EXISTS idx_message_is_read        ON core_message (is_read);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS idx_product_is_available;",
                "DROP INDEX IF EXISTS idx_product_is_featured;",
                "DROP INDEX IF EXISTS idx_product_is_promotion;",
                "DROP INDEX IF EXISTS idx_order_status;",
                "DROP INDEX IF EXISTS idx_order_payment_status;",
                "DROP INDEX IF EXISTS idx_message_is_read;",
            ],
        ),
    ]
