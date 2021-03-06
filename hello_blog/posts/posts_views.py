from flask import (Blueprint, render_template, redirect,
                   url_for, flash, abort, request)
from flask_login import login_required, current_user
from hello_blog.models import Categories, Post, Comment
from hello_blog.posts.posts_forms import (PostForm, DeletePostForm,
                                          CommentForm,
                                          UpdateCommentForm,
                                          SearchForm)


# Creates the posts blueprint
posts = Blueprint("posts", __name__)


# create the route for the main post page to show
# all recent posts to the user
@posts.route("/posts")
@login_required
def all_posts():
    form = SearchForm()
    categories = Categories.objects()
    # Paginates the results setting 4 posts per page
    page = request.args.get("page", 1, type=int)
    posts = Post.objects().order_by("-date_posted").paginate(
        page=page, per_page=4
    )
    return render_template("posts/all_posts.html",
                           title="Latest Posts",
                           posts=posts,
                           heading="Recent Posts",
                           form=form,
                           categories=categories)


# create the route to add new post
@posts.route("/post/new", methods=["GET", "POST"])
@login_required
def add_post():
    form = PostForm()
    # get categorie names for select input and loop thorough them
    categories = [(category.category_name) for category in Categories.objects]
    form.category.choices = categories

    # add the post to the database on form submit
    if form.validate_on_submit():
        category = Categories.objects(
            category_name=form.category.data).first()
        post = Post(title=form.title.data,
                    content=form.content.data,
                    author=current_user.id,
                    category=category.id)
        post.save()
        flash("post has been posted successfully", "success")
        return redirect(url_for("posts.all_posts"))
    return render_template("posts/new_post.html",
                           title="New Post",
                           form=form)


# create the route for the post page.
@posts.route("/post/<post_id>", methods=["POST", "GET"])
@login_required
def post(post_id):

    # form for deleting posts and one for adding comments
    delete_form = DeletePostForm()
    comment_form = CommentForm()
    post = Post.objects().get_or_404(id=post_id)
    comments = Comment.objects(post=post)

    # finds the amount of likes for the post
    likes = len(post.user_likes)
    is_liked = False
    comments = Comment.objects(post=post)

    # if user has liked post is_liked is true
    if post in current_user.liked_posts:
        is_liked = True

    if comment_form.validate_on_submit():
        comment = Comment(
            comment=comment_form.comment.data,
            comment_author=current_user.id,
            post=post
        )
        comment.save()
        flash("Comment posted.", "success")
        return redirect(url_for("posts.post",
                                post_id=post.id,
                                title=post.title))

    return render_template("posts/post.html",
                           title=post.title,
                           post=post,
                           delete_form=delete_form,
                           comments=comments,
                           comment_form=comment_form,
                           likes=likes,
                           is_liked=is_liked)


# create the update post route
@posts.route("/post/<post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.objects().get_or_404(id=post_id)

    # throw a 403 error if a user has managed to get to this
    #  page and they weren't the posts author.
    if post.author.id != current_user.id:
        abort(403)
    form = PostForm()
    categories = [(
        cat.category_name) for cat in Categories.objects]
    form.category.choices = categories

    #  saves post to the database on form submition
    if form.validate_on_submit():
        category = Categories.objects(
            category_name=form.category.data).first()
        post.title = form.title.data
        post.content = form.content.data
        post.category = category.id
        post.save()
        flash("Your post has been updated", "success")
        return redirect(url_for("posts.post", post_id=post.id))

    #  fills the form with the details from the database
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category.category_name

    return render_template("posts/update_post.html",
                           title="Update Post",
                           form=form)


#  create the delete post route similar to the delete user route.
@posts.route("/post/<post_id>/delete", methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    if request.method == "POST":
        post = Post.objects.get_or_404(id=post_id)
        post.delete()
        flash("Post deleted successfully", "success")
        return redirect(url_for("main.home"))
    return abort(403)


#  create the route to update comment
@posts.route("/post/<post_id>/<comment_id>/update/comment",
             methods=["POST", "GET"])
@login_required
def update_comment(post_id, comment_id):
    delete_form = DeletePostForm()
    comment_form = UpdateCommentForm()
    post = Post.objects().get_or_404(id=post_id)
    comments = Comment.objects(post=post)
    comment = Comment.objects.get_or_404(id=comment_id)

    likes = len(post.user_likes)
    is_liked = False

    if post in current_user.liked_posts:
        is_liked = True

    if request.method == "GET":
        comment_form.comment.data = comment.comment
        print(request.endpoint)

    if comment_form.validate_on_submit():
        comment.comment = comment_form.comment.data
        comment.save()
        flash("Comment has been updated", "success")
        return redirect(url_for("posts.post", post_id=post_id,
                                likes=likes, is_like=is_liked))

    return render_template("posts/post.html",
                           title="Update Comment",
                           post=post,
                           delete_form=delete_form,
                           comments=comments,
                           comment_form=comment_form,
                           likes=likes,
                           is_liked=is_liked)


# deletes the comment from the database
@posts.route("/post/<post_id>/<comment_id>/delete", methods=["GET", "POST"])
@login_required
def delete_comment(post_id, comment_id):
    comment = Comment.objects.get_or_404(id=comment_id)
    if comment.comment_author.id != current_user.id:
        abort(404)
    else:
        comment.delete()
        flash("Comment deleted successfully", "success")
        return redirect(url_for("posts.post", post_id=post_id))


# fuction to like posts
# code inspired by sante project details in readme.
@posts.route("/liked/<post_id>", methods=["GET", "POST"])
@login_required
def liked_post(post_id):
    post = Post.objects().get_or_404(id=post_id)

    # adds liked post to the users liked post array and the user details to the
    #  posts liked array

    if post not in current_user.liked_posts:
        current_user.liked_posts.append(post.id)
        current_user.save()
        post.user_likes.append(current_user.id)
        post.save()
    flash("Post liked")
    return redirect(url_for("posts.post", post_id=post.id))


# cretate posts by category route
# shows post searched by category
@posts.route("/posts/category/<category_id>")
@login_required
def category_posts(category_id):
    form = SearchForm()
    categories = Categories.objects()
    page = request.args.get('page', 1, type=int)
    category = Categories.objects(id=category_id).first_or_404()
    posts = Post.objects(category=category).order_by("-date_posted").paginate(
        page=page, per_page=4)
    return render_template("posts/posts_categories.html",
                           title=f"{category.category_name} Posts",
                           posts=posts,
                           heading=f"{category.category_name} Posts",
                           form=form,
                           category=category,
                           categories=categories)


#  create the search route
# shows post based on a text search
@posts.route("/search", methods=["GET", "POST"])
@login_required
def search():
    form = SearchForm()
    categories = Categories.objects()
    query_param = request.args.get("query")
    # gets the query paramater for paginatio
    if query_param:
        query = query_param
    # gets posts and paginates
    elif request.method == "POST":
        query = form.search.data
    page = request.args.get('page', 1, type=int)
    posts = Post.objects.search_text(query).order_by(
        '$text_score').paginate(page=page, per_page=4)
    print(posts)
    # if no posts are found in search it redirects to current page and
    # flashes a message
    if not posts.items:
        flash("No results Found. Please search again", "errors")
        return redirect(request.referrer)
    return render_template("posts/search_results.html",
                           title="Search Results",
                           posts=posts,
                           heading="Search Results",
                           form=form,
                           categories=categories,
                           query=query)


# code from stack overflow to stop cache on safari
@posts.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
