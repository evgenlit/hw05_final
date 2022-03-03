from http import HTTPStatus

from django.test import TestCase


class PostURLTests(TestCase):

    def setUp(self):
        self.unexisting_page = '/unexisting_page/'
        self.template404 = 'core/404.html'

    def test_unexisting_page_correct_response_code(self):
        """Проверяем, что не существующая страница
           отдает корректный статус"""
        response = self.client.get(self.unexisting_page)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_url_use_correct_template(self):
        """Проверяем, что не существующая страница
            использует соответствующий шаблон."""
        response = self.client.get(self.unexisting_page)

        self.assertTemplateUsed(response, self.template404)
