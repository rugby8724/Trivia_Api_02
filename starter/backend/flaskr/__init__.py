import os
from flask import Flask, request, abort, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    """
    Uses QUESTIONS_PER_PAGE to determine how many questions to display
    per page.
    """
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headders', 'Content-Type, Authorization')
      response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
      return response

  '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
      """
      Displays all quiz categories
      Will abort if no categories are found
      """
      category_info = Category.query.order_by(Category.id).all()

      if len(category_info) == 0:
          abort(404)

      categories = [category.format() for category in category_info]

      return jsonify({
        'success': True,
        'categories': categories,
        'total_categories': len(Category.query.all())
      })



  '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
  @app.route('/questions', methods=['GET'])
  def get_questions():
      '''
      Displays all questions
      will paginate questions using def paginate_questions
      will abort if no questions are found
      '''

      selection = Question.query.order_by(Question.category).all()
      current_questions = paginate_questions(request, selection)

      if len(current_questions) == 0:
          abort(404)

      category_info = Category.query.order_by(Category.id).all()
      category_names = {}

      for item in category_info:
          category_names[str(item.id)] = item.type

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
        'categories': 'All Categories Selected',
        'current_category': category_names
      })


  '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_questions(question_id):
      '''
      Delete question by questions id
      Will abort if question id is not found
      '''
      try:
          question = Question.query.get_or_404(question_id)

          if question is None:
              abort(404)

          question.delete()
          selection = Question.query.order_by(Question.category).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
            'success': True,
            'deleted_question': question_id,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'selected_categories': 'All Categories Selected'
          })
      except:
          abort(422)



  '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

  @app.route('/questions', methods=['POST'])
  def create_question():
      '''
      Will create or search for questions
      If search is used questions will be paginated using def paginate_questions
      '''
      body = request.get_json()

      question = body.get('question')
      answer = body.get('answer')
      category = body.get('category')
      difficulty = body.get('difficulty')
      search = body.get('searchTerm')


      if search:
          selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search)))
          current_questions = paginate_questions(request, selection)

          return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection.all())
          })



      if not question or not answer or not category or not difficulty:
              abort(400)


      try:
          question = Question(question=question, answer=answer,
                       difficulty=difficulty, category=category)

          question.insert()


          return jsonify({
            'success': True,
            'question': question.format()
            })

      except:
          abort(422)


  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''


  '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def questions_by_category(category_id):
      '''
      Gets questions by category_id
      Paginates questions using def paginate_questions
      Aborts if no quetions are found
      '''
      selection = Question.query.filter(Question.category == category_id).all()
      current_questions = paginate_questions(request, selection)

      if len(current_questions) == 0:
          abort(404)

      category = Category.query.get_or_404(category_id)
      category_name = category.type

      return jsonify ({
        'success': True,
        'questions': current_questions,
        'total_questions': len(current_questions),
        'current_category': category_name
      })


  '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
  @app.route('/play_quiz', methods=['POST'])
  def get_quiz_next_question():

    body = request.get_json()
    previous_questions = body.get('previous_questions', None)
    quiz_category = body.get('quiz_category', None)

    if previous_questions is None or quiz_category is None:
        abort(400)

    try:
        quiz_category_id = int(quiz_category["id"])
    except (KeyError, ValueError):
        abort(400)

    if (not isinstance(previous_questions, list) and
            all(isinstance(previous_question, int) for
                previous_question in previous_questions)):
        abort(400)

    if len(previous_questions) > 0:
        if quiz_category_id is 0:  # query all categories
            next_question = (Question.query.
                             filter(~Question.id.in_(previous_questions)).
                             order_by(func.random()).first_or_404())
        else:
            next_question = (Question.query.
                             filter(Question.category == quiz_category_id,
                                    ~Question.id.in_(previous_questions)).
                             order_by(func.random()).first_or_404())
    else:
        if quiz_category_id is 0:  # query all categories
            next_question = (Question.query.
                             order_by(func.random()).first_or_404())
        else:
            next_question = (Question.query.
                             filter(Question.category == quiz_category_id).
                             order_by(func.random()).first_or_404())

    return jsonify({
      "success": True,
      "question": next_question.format()
    })





  '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
      }), 404
  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
      })

  return app
