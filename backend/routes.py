import logging

from app import app, db , socketio ,allowed_file, redis
from flask_socketio import emit, join_room, leave_room
from flask import request, jsonify, session
from models import *
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import allowed_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from marshmallow import Schema, fields, ValidationError
from models import *

# register
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
        print(user_id)
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

    return jsonify([{
        'id': tweet.id,
        'user_id': tweet.user_id,
        'text_content': tweet.text_content,
        'media_content': tweet.media_content
    } for tweet in tweets])

# like tweet
@app.route("/api/likes", methods = ["POST"])
def like_tweet():
    data = request.json
    user_id = data.get("user_id")
    tweet_id = data.get("tweet_id")
    if not user_id or not tweet_id:
        return jsonify({'status':'error', 'message':'user_id and tweet_id are required'})
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'status':'error', 'message':'user_id not available'})
    
    tweet = Tweet.query.filter_by(id=tweet_id).first()
    if not tweet:
        return jsonify({'status':'error', 'message':'tweet_id not available'})
    
    if tweet in user.liked_tweets:
        user.liked_tweets.remove(tweet)
        db.session.commit()
        return jsonify({'status':'success', 'message':'tweet unliked successfully'})
    else:
        user.liked_tweets.append(tweet)
        db.session.commit()
        return jsonify({'status':'success', 'message':'tweet liked successfully'})
    
# like bosgan tweetimizni olish
# get liked tweets
@app.route("/api/likes/<user_id>", methods = ["GET"])
def get_liked_tweets(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'status':'error', 'message':'user_id not available'})
    liked_tweets = user.liked_tweets
    liked_tweets_list = []
    for tweet in liked_tweets:
        liked_tweets_list.append(tweet.to_dict())
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
        user = User.query.filter_by(id = user_id).first()
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


# tweetning barcha ma'lumotlarini olish + replylar, retweetlar, likelar
@app.route("/api/<int:tweet_id>/data", methods = ["GET"])
def tweet_data(tweet_id):
    try:
        tweet = Tweet.query.filter_by(id = tweet_id).first()
        if not tweet:
            return jsonify({'status':'error', 'message':'tweet_id is not found'})
        
        reply_count = Reply.query.filter_by(tweet_id = tweet_id).count()
        retweet_count = Retweet.query.filter_by(tweet_id = tweet_id).count()
        like_count = Like.query.filter_by(tweet_id = tweet_id).count()
        view_count = View.query.filter_by(tweet_id = tweet_id).count()

        data = {
            'tweet_id':tweet_id,
            'user_id':tweet.user_id,
            'text_content':tweet.text_content,
            'media_content':tweet.media_content,
            'reply_count':reply_count,
            'retweet_count':retweet_count,
            'like_count':like_count,
            'view_count':view_count
        }
        return jsonify({'status':'success', 'message':'tweet data received succesfully', 'data':data})
    
    except:
        return jsonify({'status':'error', 'message':'Something went wrong'})




logger = logging.getLogger(__name__)

class CreateGroupSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x) > 0)
    member_ids = fields.List(fields.Int, required=True, validate=lambda x: len(x) > 0)

class MessageSchema(Schema):
    receiver_id = fields.Int(allow_none=True)
    group_id = fields.Int(allow_none=True)
    content = fields.Str(allow_none=True)
    media_url = fields.Str(allow_none=True)

class ReactionSchema(Schema):
    message_id = fields.Int(required=True)
    emoji = fields.Str(required=True, validate=lambda x: len(x) > 0)

class DeleteMessageSchema(Schema):
    message_id = fields.Int(required=True)
    delete_for_all = fields.Boolean(default=False)

class EditMessageSchema(Schema):
    message_id = fields.Int(required=True)
    new_content = fields.Str(required=True)

def error_response(message, status_code):
    return jsonify({'error': {'message': message, 'code': status_code}}), status_code

def get_room_name(user_id=None, receiver_id=None, group_id=None):
    if receiver_id:
        return f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    return f"group_{group_id}"

@app.route('/api/create_group', methods=['POST'])
@jwt_required()
def create_group():
    current_user_id = get_jwt_identity()
    try:
        data = CreateGroupSchema().load(request.get_json())
    except ValidationError as err:
        return error_response(err.messages, 400)

    try:
        group = Group(name=data['name'])
        db.session.add(group)
        db.session.commit()

        # Foydalanuvchilarni guruhga qo'shish
        for user_id in data['member_ids']:
            if not User.query.get(user_id):
                db.session.rollback()
                return error_response(f"User {user_id} not found", 404)
            member = GroupMembers(user_id=user_id, group_id=group.id)
            db.session.add(member)

        # Guruh yaratuvchisini qo'shish
        member = GroupMembers(user_id=current_user_id, group_id=group.id)
        db.session.add(member)

        db.session.commit()
        logger.info(f"Group {group.name} created by user {current_user_id}")
        return jsonify({'message': 'Group created', 'group_id': group.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating group: {str(e)}")
        return error_response(str(e), 500)

@app.route('/api/messages/<int:user_id>/<int:receiver_id>', methods=['GET'])
@jwt_required()
def get_messages(user_id, receiver_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return error_response("Unauthorized access", 403)

    # Bloklanganligini tekshirish
    if Block.query.filter_by(blocker_id=receiver_id, blocked_id=user_id).first():
        return error_response("You are blocked by this user", 403)

    try:
        messages = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == user_id))
        ).filter(Message.group_id == None).options(joinedload(Message.reactions)).order_by(Message.timestamp.asc()).all()

        deleted_messages = {dm.message_id for dm in DeletedMessage.query.filter_by(user_id=user_id).all()}

        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id,
            'content': msg.content,
            'media_url': msg.media_url,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'reactions': [{'user_id': r.user_id, 'emoji': r.emoji} for r in msg.reactions]
        } for msg in messages if msg.id not in deleted_messages]), 200
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return error_response(str(e), 500)



@app.route('/api/group_messages/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    current_user_id = get_jwt_identity()
    if not GroupMembers.query.filter_by(user_id=current_user_id, group_id=group_id).first():
        return error_response("Not a group member", 403)

    try:
        messages = Message.query.filter_by(group_id=group_id).options(joinedload(Message.reactions)).order_by(Message.timestamp.asc()).all()
        deleted_messages = {dm.message_id for dm in DeletedMessage.query.filter_by(user_id=current_user_id).all()}

        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'group_id': msg.group_id,
            'content': msg.content,
            'media_url': msg.media_url,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': MessageReadStatus.query.filter_by(message_id=msg.id, user_id=current_user_id).first().is_read if MessageReadStatus.query.filter_by(message_id=msg.id, user_id=current_user_id).first() else False,
            'reactions': [{'user_id': r.user_id, 'emoji': r.emoji} for r in msg.reactions]
        } for msg in messages if msg.id not in deleted_messages]), 200
    except Exception as e:
        logger.error(f"Error fetching group messages: {str(e)}")
        return error_response(str(e), 500)

@app.route('/api/upload_media', methods=['POST'])
@jwt_required()
def upload_media():
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    if 'file' not in request.files:
        return error_response("No file part in the request", 400)

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return error_response("Invalid or no selected file", 400)

    if file.content_length and file.content_length > MAX_FILE_SIZE:
        return error_response("File size exceeds 5MB limit", 400)

    try:
        filename = f"{datetime.utcnow().timestamp()}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logger.info(f"File {filename} uploaded by user {get_jwt_identity()}")
        return jsonify({'media_url': f"/Uploads/{filename}"}), 200
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return error_response("Failed to upload file", 500)

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