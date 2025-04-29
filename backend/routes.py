from app import app, db, socketio
from flask_socketio import emit, join_room, leave_room
from flask import request, jsonify, session
from models import *
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import allowed_file




# @app.route("/api/auth/check-user", methods = ["POST"])
# def check_user():
#     data = request.get_json()
#     email = data.get("email")
#     full_name = data.get("name")
#     user = User.query.filter_by(email=email, full_name=full_name).first()
#     if not user :
#         return jsonify({
#             'status': 'error',
#             'message': 'user not found'
#         })
#     return jsonify({
#         'status': 'success',
#         'message': 'user found',
#         'user': {
#             'user_id': user.user_id,
#             'username': user.username,
#             'email': user.email,
#             'full_name': user.full_name,
#             'profile_image_url': user.profile_image_url
#         }
#     })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id is required'}), 400
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    bio = data.get("bio")  
    profile_image_url = data.get("profile_image_url")

    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'username, email, password are required'})

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'status': 'error', 'message': 'username already exists'})

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'status':'error', 'message':'email already exists'})

    # username checking
    for i in username:
        if (not i.isdigit()) and (not i.isalpha()):
            return jsonify({'status':'error', 'message':'username can contain only letter and digit'})
    if len(username) < 5:
        return jsonify({'status':'error', 'message':'username must be at least 5 characters long'})
    if not username[0].isalpha():
        return jsonify({'status':'error', 'message':'username must start with a letter'})
    
    # password checking
    pass_let, pass_num = 0, 0
    for i in password:
        if i.isalpha(): pass_let += 1
        elif i.isdigit(): pass_num += 1
    if len(password) < 8 or pass_let == 0 or pass_num == 0:
        return jsonify({'status':'error', 'message':'password must be at least 8 characters long and contain at least one letter and one digit'})

    user = User(
        user_id=data['user_id'], 
        username=username,
        email=email,
        full_name=full_name,
        bio=bio,
        profile_image_url=profile_image_url
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'succesfully created account', "user":{
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'bio': user.bio,
        'profile_image_url': user.profile_image_url
    }})


# login
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if username:
        user = User.query.filter_by(username=username).first()
    elif email:
        user = User.query.filter_by(email=email).first()
    else:
        return jsonify({'status': 'error', 'message': 'username or email required'})

    # Add this check
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'})

    if user.check_password(password):
        return jsonify({
            'status': 'success',
            'message': 'successfully logged in',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'profile_image_url': user.profile_image_url
            }
        })
    
    else:
        return jsonify({'status': 'error', 'message': 'credentials do not match'})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    try:
        response = jsonify({
            'status': 'success',
            'message': 'Successfully logged out'
        })
        return response, 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Logout failed: {str(e)}'
        }), 500


# create tweet
@app.route('/api/tweets', methods=['POST'])
def create_tweet():
    try:
        content = request.form.get('content')
        user_id = request.form.get('user_id')
        
        if not content or not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Content and user_id are required'
            }), 400
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Create a safe filename with timestamp
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                    # Save the file
                file.save(file_path)
                
                # Generate proper URL for the frontend
                image_url = f"http://localhost:5000/uploads/{filename}"

        new_tweet = Tweet(
            user_id=user_id,
            text_content=content,
            media_content=image_url,
            # user=user
        )
        
        db.session.add(new_tweet)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Tweet created successfully',
            'tweet': new_tweet.to_json()
        })

    except Exception as e:
        print(f"Error creating tweet: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

# edit tweet
@app.route("/api/tweet/<id>", methods=["PATCH"])
def edit_tweet(id):
    data = request.json
    text_content = data.get("text_content")
    media_content = data.get("media_content")  # media link

    if not text_content and not media_content:
        return jsonify({'status': 'error', 'message': 'text_content or media_content are required'})

    tweet = Tweet.query.filter_by(id=id).first()

    tweet.text_content = text_content
    tweet.media_content = media_content
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'tweet updated successfully'})


# delete tweet
@app.route("/api/tweet/<id>", methods=["DELETE"])
def delete_tweet(id):
    tweet = Tweet.query.filter_by(id=id).first()
    if tweet:
        db.session.delete(tweet)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'tweet deleted successfully'})

    else:
        return jsonify({'status': 'error', 'message': 'tweet is not available'})


# get tweets
@app.route("/api/tweets/<user_id>", methods=["GET"])
def get_user_tweets(user_id):
    tweets = Tweet.query.filter_by(user_id=user_id).all()
    if not tweets:
        return jsonify({'status': 'error', 'message': 'no tweets found'})

    return jsonify({
        'status': 'success',
        'message': 'tweets received successfully',
        "tweets": [tweet.to_json() for tweet in tweets[::-1]]
    })

# like tweet
@app.route("/api/likes", methods = ["POST"])
def like_tweet():
    data = request.json
    user_id = data.get("user_id")
    tweet_id = data.get("tweet_id")
    if not user_id or not tweet_id:
        return jsonify({'status':'error', 'message':'user_id and tweet_id are required'})
    
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'status':'error', 'message':'user_id not available'})
    
    tweet = Tweet.query.filter_by(id=tweet_id).first()
   
    if not tweet:
        return jsonify({'status':'error', 'message':'tweet_id not available'})


    liked_tweet = Like.query.filter_by(user_id=user_id, tweet_id=tweet_id).first()
    
    if liked_tweet:
        db.session.delete(liked_tweet)
        db.session.commit()
        return jsonify({'status':'success', 'message':'tweet unliked successfully'})
    else:
        like = Like(user_id=user_id, tweet_id=tweet_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'status':'success', 'message':'tweet liked successfully'} )
    
# like bosgan tweetimizni olish
# get liked tweets
@app.route("/api/likes/<user_id>", methods = ["GET"])
def get_liked_tweets(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'status':'error', 'message':'user_id not available'})
    liked_tweets = Like.query.filter_by(user_id=user_id).all()
    liked_tweets_list = []
    for like in liked_tweets:
        liked_tweets_list.insert(0, Tweet.query.filter_by(id=like.tweet_id).first().to_json())
    return jsonify({'status':'success', 'liked_tweets':liked_tweets_list})

# Barcha tweetlarni olish
# get all tweets
@app.route("/api/tweets", methods = ["GET"])
def get_tweets():
    tweets = Tweet.query.all()
    tweets_list = []
    for tweet in tweets:
        tweets_list.append(tweet.to_json())
    return jsonify({'status':'success', 'tweets':tweets_list[::-1]})


@app.route("/api/follow", methods = ["POST"])
def follow():
    try: 
        data = request.json
        follower_id = data.get("follower_id")
        following_id = data.get("following_id")

        if not follower_id or not following_id:
            return jsonify({'status':'error', 'message':'follower_id and following_id are required'})
        
        if follower_id == following_id:
            return jsonify({'status':'error', 'message':'follower_id and following_id cannot be equal'})
        
        user = User.query.filter_by(id=follower_id).first()
        if not user:
            return jsonify({'status':'error', 'message':'follower_id not available'})
        
        user = User.query.filter_by(id=following_id).first()
        if not user:
            return jsonify({'status':'error', 'message':'following_id not available'})

        follow = db.session.query(Follower).filter(Follower.follower_id == follower_id, Follower.following_id == following_id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return jsonify({'status':'success', 'message':'unfollowed successfully'})
        else:
            follow = Follower(follower_id = follower_id, following_id = following_id)
            db.session.add(follow)
            db.session.commit()
            return jsonify({'status':'success', 'message':'followed successfully'})
    except:
        return jsonify({'status':'error', 'message':'something went wrong'})


@app.route("/api/follow/<user_id>", methods = ["GET"])
def get_follows(user_id):
    try:
        follows = Follower.query.filter_by(follower_id = user_id).all()
        if follows:
            follow_ids = []
            for i in follows: follow_ids.append(i.following_id)
            return jsonify({'status':'success', 'message':'succesfully received data', 'data':follow_ids})
        else:
            return jsonify({'status':'error', 'message':'this user has no followings'})
    except Exception as e:
        return jsonify({'status':'error', 'message':f'something went wrong: {e}'})


@app.route("/api/reply", methods = ["POST"])
def reply():
    try:
        data = request.json
        user_id = data.get("user_id")
        tweet_id = data.get("tweet_id")
        text_content = data.get("text_content")
        media_content = data.get("media_content")
        if not user_id or not tweet_id or not text_content:
            return jsonify({'status':'error', 'message':'user_id, tweet_id, text_content are required'})
        user = User.query.filter_by(user_id = user_id).first()
        if not user:
            return jsonify({'status':'error', 'message':'user_id is not available'})
        tweet = Tweet.query.filter_by(id = tweet_id).first()
        if not tweet:
            return jsonify({'status':'error', 'message':'tweet_id is not available'})
        reply = Reply(user_id = user_id, tweet_id = tweet_id, text_content = text_content, media_content = media_content)
        db.session.add(reply)
        db.session.commit()
        return jsonify({'status':'success', 'message':'replied succesfully'})
    except Exception as e:
        return jsonify({'status':'error', 'message':'Something went wrong'})


@app.route("/api/<int:tweet_id>/replies", methods = ["GET"])
def tweet_replies(tweet_id):
    try:
        tweet = Tweet.query.filter_by(id = tweet_id).first()
        if not tweet:
            return jsonify({'status':'error', 'message':'tweet_id is not available'})
        replies = Reply.query.filter_by(tweet_id = tweet_id).all()
        data = []
        for i in replies:
            data.append({'user_id':i.user_id, 'tweet_id':i.tweet_id, 'text_content':i.text_content})
        if replies:
            return jsonify({'status':'success', 'message':'replies data reseived succesfully', 'data':data})
        else:
            return jsonify({'status':'error', 'message':'this post has no replies'})
    except:
        return jsonify({'status':'error', 'message':'Something went wrong'})


# @app.route("/api/replies/<user_id>", methods = ["GET"])
# def get_user_replies(user_id):
#     try:
#         user = User.query.filter_by(user_id = user_id).first()
#         if not user:
#             return jsonify({'status':'error', 'message':'user_id is not available'})
#         replies = Reply.query.filter_by(user_id = user_id).all()
#         data = []
#         for i in replies:
#             data.append({'user_id':i.user_id, 'tweet_id':i.tweet_id, 'text_content':i.text_content})
#         if replies:
#             return jsonify({'status':'success', 'message':'replies data reseived succesfully', 'data':data})
#         else:
#             return jsonify({'status':'error', 'message':'this user has no replies'})
#     except:
#         return jsonify({'status':'error', 'message':'Something went wrong'})

@app.route("/api/replies/<user_id>", methods=["GET"])
def get_user_replies(user_id):
    try:
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'user_id not available'})

        replies = Reply.query.filter_by(user_id=user_id).all()
        if not replies:
            return jsonify({
                'status': 'success',
                'replies': []
            })

        replies_data = []
        for reply in replies:
            tweet = Tweet.query.filter_by(id=reply.tweet_id).first()
            tweeted_user = User.query.filter_by(user_id=tweet.user_id).first()
            if tweet:
                reply_data = {
                    'id': reply.id,
                    'text_content': reply.text_content,
                    'media_content': reply.media_content,
                    'created_at': reply.replied_at,
                    'user': {
                        'username': user.username,
                        'profile_image_url': user.profile_image_url
                    },
                    'original_tweet': {
                        'id': tweet.id,
                        'text_content': tweet.text_content,
                        'media_content': tweet.media_content,
                        'created_at': tweet.created_at,
                        'user': {
                            'username': tweeted_user.username,
                            'profile_image_url': tweeted_user.profile_image_url
                        }
                    }
                }
                replies_data.append(reply_data)

        return jsonify({
            'status': 'success',
            'replies': replies_data
        })

    except Exception as e:
        print(f"Error in get_user_replies: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Something went wrong'
        }), 500


# tweetning barcha ma'lumotlarini olish + replylar, retweetlar, likelar
@app.route("/api/<int:tweet_id>/data", methods=["GET"])
def tweet_data(tweet_id):
    try:
        tweet = Tweet.query.filter_by(id=tweet_id).first()
        if not tweet:
            return jsonify({'status': 'error', 'message': 'Tweet not found'})

        current_user_id = request.args.get("user_id")
        if not current_user_id:
            return jsonify({'status': 'error', 'message': 'user_id is missing'})
        try:
            view_count = View.query.filter_by(user_id=current_user_id, tweet_id=tweet_id).first()
            if not view_count:
                view = View(user_id=current_user_id, tweet_id=tweet_id)
                db.session.add(view)
                db.session.commit()
        except Exception as e:
            print(f"Error adding view: {str(e)}")
            db.session.rollback()

        reply_count = Reply.query.filter_by(tweet_id=tweet_id).count()
        retweet_count = Retweet.query.filter_by(tweet_id=tweet_id).count()
        like_count = Like.query.filter_by(tweet_id=tweet_id).count()
        view_count = View.query.filter_by(tweet_id=tweet_id).count()

        is_liked = Like.query.filter_by(user_id=current_user_id, tweet_id=tweet_id).first() is not None
        is_retweeted = Retweet.query.filter_by(user_id=current_user_id, tweet_id=tweet_id).first() is not None
        is_bookmarked = Bookmark.query.filter_by(user_id=current_user_id, tweet_id=tweet_id).first() is not None

        data = {
            'tweet_id': tweet_id,
            'user_id': tweet.user_id,
            'text_content': tweet.text_content,
            'media_content': tweet.media_content,
            'reply_count': reply_count,
            'retweet_count': retweet_count,
            'like_count': like_count,
            'view_count': view_count
        }

        return jsonify({
            'status': 'success',
            'message': 'Tweet data fetched successfully',
            'data': data,
            'is_liked': is_liked,
            'is_retweeted': is_retweeted,
            'is_bookmarked': is_bookmarked
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/bookmarks', methods=['POST'])
def add_to_bookmark():
    data = request.get_json()  
    user_id = data.get('user_id')
    tweet_id = data.get('tweet_id')
    if not user_id or not tweet_id:
        return jsonify({'status': 'error', 'message': 'user_id and tweet_id are required'}), 400
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'user_id not available'}), 404
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    if not tweet:
        return jsonify({'status': 'error', 'message': 'tweet_id not available'}), 404
    bookmark = Bookmark.query.filter_by(user_id=user_id, tweet_id=tweet_id).first()
    is_bookmarked = Bookmark.query.filter_by(user_id=user_id, tweet_id=tweet_id).first() is not None
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        print(is_bookmarked)
        return jsonify({'status': 'success', 'message': 'removed from bookmarks'}), 200
    else:
        bookmark = Bookmark(user_id=user_id, tweet_id=tweet_id)
        db.session.add(bookmark)
        db.session.commit()
        print(is_bookmarked)
        return jsonify({'status': 'success', 'message': 'added to bookmarks'}), 200
@app.route("/api/bookmarks/", methods=['GET'])
def get_bookmarks():
    user_id = request.args.get('user_id')
    user = User.query.filter_by(user_id = user_id).first()
    if not user:
        return jsonify({'status':'error', 'message':'user_id not available'})
    bookmarks = Bookmark.query.filter_by(user_id = user_id).all()
    if not bookmarks:
        return jsonify({'status':'error', 'message':'this user has no bookmarks'})
    tweet_list = [Tweet.query.filter_by(id = i.tweet_id).first().to_json() for i in bookmarks]
    return jsonify({'status':'success', 'message':'bookmarks data received successfully', 'tweet_list':tweet_list[::-1]})
@app.route('/api/create_group', methods=['POST'])
def create_group():
    data = request.get_json()
    name = data.get('name')
    member_ids = data.get('member_ids')  # [1, 2, 3]

    group = Group(name=name)
    db.session.add(group)
    db.session.flush()

    for user_id in member_ids:
        member = GroupMembers(user_id=user_id, group_id=group.id)
        db.session.add(member)

    db.session.commit()
    return jsonify({'message': 'Group created', 'group_id': group.id}), 201

@app.route('/api/messages/<int:user_id>/<int:receiver_id>', methods=['GET'])
def get_messages(user_id, receiver_id):
    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == user_id))
    ).filter(Message.group_id == None).order_by(Message.timestamp.asc()).all()

    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'content': msg.content,
        'media_url': msg.media_url,
        'timestamp': msg.timestamp.isoformat(),
        'is_read': msg.is_read,
        'reactions': [{'user_id': r.user_id, 'emoji': r.emoji} for r in Reaction.query.filter_by(message_id=msg.id).all()]
    } for msg in messages if str(user_id) not in msg.deleted_for.split(',')]), 200


@app.route('/api/group_messages/<int:group_id>', methods=['GET'])
def get_group_messages(group_id):
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc()).all()
    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'group_id': msg.group_id,
        'content': msg.content,
        'media_url': msg.media_url,
        'timestamp': msg.timestamp.isoformat(),
        'is_read': msg.is_read,
        'reactions': [{'user_id': r.user_id, 'emoji': r.emoji} for r in Reaction.query.filter_by(message_id=msg.id).all()]
    } for msg in messages]), 200

@app.route('/api/upload_media', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'media_url': f"/{app.config['UPLOAD_FOLDER']}/{filename}"}), 200

@socketio.on('join')
def on_join(data):
    user_id = data['user_id']
    receiver_id = data.get('receiver_id')  # 1:1 chat uchun
    group_id = data.get('group_id')  # Guruh chat uchun

    if receiver_id:
        room = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    else:
        room = f"group_{group_id}"

    join_room(room)
    emit('status', {'message': f'Joined room {room}'}, room=room)

@socketio.on('leave')
def on_leave(data):
    user_id = data['user_id']
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')

    if receiver_id:
        room = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    else:
        room = f"group_{group_id}"

    leave_room(room)
    emit('status', {'message': f'Left room {room}'}, room=room)

@socketio.on('typing')
def handle_typing(data):
    user_id = data['user_id']
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')

    if receiver_id:
        room = f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    else:
        room = f"group_{group_id}"

    user = User.query.get(user_id)
    emit('typing', {'username': user.username, 'is_typing': True}, room=room, skip_sid=request.sid)

@socketio.on('send_message')
def handle_message(data):
    sender_id = data['sender_id']
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    content = data.get('content')
    media_url = data.get('media_url')

    new_message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        group_id=group_id,
        content=content,
        media_url=media_url
    )
    db.session.add(new_message)
    db.session.commit()

    if receiver_id:
        room = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
    else:
        room = f"group_{group_id}"

    emit('receive_message', {
        'id': new_message.id,
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'group_id': group_id,
        'content': content,
        'media_url': media_url,
        'timestamp': new_message.timestamp.isoformat(),
        'is_read': new_message.is_read
    }, room=room)

    # Bildirishnoma yuborish
    emit('notification', {'message': 'New message received', 'from_user_id': sender_id}, room=room)

@socketio.on('read_message')
def handle_read_message(data):
    message_id = data['message_id']
    user_id = data['user_id']

    message = Message.query.get(message_id)
    if message and (message.receiver_id == user_id or message.group_id):
        message.is_read = True
        db.session.commit()

        room = f"chat_{min(message.sender_id, message.receiver_id)}_{max(message.sender_id, message.receiver_id)}" if message.receiver_id else f"group_{message.group_id}"
        emit('message_read', {'message_id': message_id, 'is_read': True}, room=room)

@socketio.on('add_reaction')
def handle_reaction(data):
    message_id = data['message_id']
    user_id = data['user_id']
    emoji = data['emoji']

    reaction = Reaction(message_id=message_id, user_id=user_id, emoji=emoji)
    db.session.add(reaction)
    db.session.commit()

    message = Message.query.get(message_id)
    room = f"chat_{min(message.sender_id, message.receiver_id)}_{max(message.sender_id, message.receiver_id)}" if message.receiver_id else f"group_{message.group_id}"
    emit('reaction_added', {'message_id': message_id, 'user_id': user_id, 'emoji': emoji}, room=room)

@socketio.on('delete_message')
def handle_delete_message(data):
    message_id = data['message_id']
    user_id = data['user_id']
    delete_for_all = data.get('delete_for_all', False)

    message = Message.query.get(message_id)
    if message.sender_id != user_id:
        return

    if delete_for_all:
        db.session.delete(message)
    else:
        message.deleted_for = f"{message.deleted_for},{user_id}" if message.deleted_for else str(user_id)
    db.session.commit()

    room = f"chat_{min(message.sender_id, message.receiver_id)}_{max(message.sender_id, message.receiver_id)}" if message.receiver_id else f"group_{message.group_id}"
    emit('message_deleted', {'message_id': message_id, 'delete_for_all': delete_for_all}, room=room)

@socketio.on('edit_message')
def handle_edit_message(data):
    message_id = data['message_id']
    user_id = data['user_id']
    new_content = data['new_content']

    message = Message.query.get(message_id)
    if message.sender_id != user_id:
        return

    message.content = new_content
    db.session.commit()

    room = f"chat_{min(message.sender_id, message.receiver_id)}_{max(message.sender_id, message.receiver_id)}" if message.receiver_id else f"group_{message.group_id}"
    emit('message_edited', {'message_id': message_id, 'new_content': new_content}, room=room)


@app.route('/api/block/<int:blocker_id>/<int:blocked_id>', methods=['POST'])
def block_user(blocker_id, blocked_id):
    if blocker_id == blocked_id:
        return jsonify({'error': 'Cannot block yourself'}), 400

    block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
    db.session.add(block)
    db.session.commit()
    return jsonify({'message': 'User blocked'}), 200

@app.route('/api/unread_count/<int:user_id>', methods=['GET'])
def unread_count(user_id):
    unread = Message.query.filter(
        (Message.receiver_id == user_id) & (Message.is_read == False)
    ).count()
    return jsonify({'unread_count': unread}), 200


@app.route('/api/retweet', methods=['POST'])
def retweet():
    try:
        data = request.json
        user_id = data.get("user_id")
        tweet_id = data.get("tweet_id")
        if not user_id or not tweet_id:
            return jsonify({'status':'error', 'message':'user_id and tweet_id are required'})
        
        retweet = Retweet.query.filter_by(user_id=user_id, tweet_id=tweet_id).first()
        if retweet:
            db.session.delete(retweet)
            db.session.commit()
            return jsonify({'status':'success', 'message':'retweet removed successfully'})
        else:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return jsonify({'status':'error', 'message':'user_id is not available'})
            
            tweet = Tweet.query.filter_by(id=tweet_id).first()
            if not tweet:
                return jsonify({'status':'error', 'message':'tweet_id is not available'})
            retweet = Retweet(user_id=user_id, tweet_id=tweet_id)
            db.session.add(retweet)
            db.session.commit()
    except:
        return jsonify({'status':'error', 'message':'something went wrong'})
    return jsonify({'status':'success', 'message':'retweet successfully'})


@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'user_id not available'}), 404

        tweets = Tweet.query.filter_by(user_id=user_id).all()
        data = []
        for tweet in tweets:
            data.insert(0, tweet.to_json())

        followers = Follower.query.filter_by(following_id=user_id).all()
        follower_count = len(followers)

        following = Follower.query.filter_by(follower_id=user_id).all()
        following_count = len(following)

        return jsonify({
            'status': 'success',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'bio': user.bio,
                'profile_image_url': user.profile_image_url,
                'posts': data,
                'follower_count': follower_count,
                'following_count': following_count,
                'post_count': len(data)
            }
        }), 200
    except:
        return jsonify({'status': 'error', 'message': 'something went wrong'}), 500
@app.route("/api/edit/profile/<user_id>", methods=["PUT"])
def edit_profile(user_id):
    full_name = request.form.get("full_name")
    bio = request.form.get("bio")
    user = User.query.filter_by(user_id=user_id).first()
    
    if not user:
        return jsonify({"status": "error", "message": "User is not found"})
    
    # Обработка загрузки аватара
    if 'profile_image_url' in request.files:
        avatar_file = request.files['profile_image_url']
        if avatar_file and allowed_file(avatar_file.filename):
            # Создаем безопасное имя файла с временной меткой
            filename = secure_filename(f"{datetime.now().timestamp()}_avatar_{avatar_file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Сохраняем файл
            avatar_file.save(file_path)
            
            # Генерируем URL для фронтенда
            user.profile_image_url = f"http://localhost:5000/uploads/{filename}"
    
    # Обработка загрузки баннера
    if 'banner_image_url' in request.files:
        banner_file = request.files['banner_image_url']
        if banner_file and allowed_file(banner_file.filename):
            # Создаем безопасное имя файла с временной меткой
            filename = secure_filename(f"{datetime.now().timestamp()}_banner_{banner_file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Сохраняем файл
            banner_file.save(file_path)
            
            # Генерируем URL для фронтенда
            user.banner_image_url = f"http://localhost:5000/uploads/{filename}"
    
    # Обновляем текстовые поля
    user.full_name = full_name
    user.bio = bio
    
    db.session.commit()
    
    return jsonify({
        "status": "success", 
        "message": "Profile edited successfully", 
        "user": {
            "profile_image_url": user.profile_image_url, 
            "banner_image_url": user.banner_image_url,
            "full_name": user.full_name
        }
    })