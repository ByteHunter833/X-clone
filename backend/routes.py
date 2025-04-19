import logging

from app import app, db , socketio , redis
from flask_socketio import emit, join_room, leave_room
from flask import request, jsonify, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import allowed_file
from sqlalchemy.orm import joinedload
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
    data = request.get_json()  # request.json o'rniga get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username and not email:
        return jsonify({'status': 'error', 'message': 'username or email required'}), 400

    try:
        if username:
            user = User.query.filter_by(username=username).first()
        else:
            user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'status': 'error', 'message': 'user not found'}), 404

        if user.check_password(password):
            logger.info(f"User {user.username} logged in successfully")
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
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'credentials do not match'}), 401
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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

def error_response(message, status_code):
    return jsonify({'error': {'message': message, 'code': status_code}}), status_code

# Xona nomini aniqlash funksiyasi
def get_room_name(user_id=None, receiver_id=None, group_id=None):
    if receiver_id:
        return f"chat_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
    return f"group_{group_id}"

# Guruh yaratish
@app.route('/api/create_group', methods=['POST'])
def create_group():
    data = request.get_json()

    if not data or 'name' not in data or not isinstance(data['name'], str) or len(data['name'].strip()) == 0:
        return error_response("Group name is required and must be a non-empty string", 400)
    if 'member_ids' not in data or not isinstance(data['member_ids'], list) or len(data['member_ids']) == 0:
        return error_response("Member IDs are required and must be a non-empty list", 400)
    if not all(isinstance(user_id, int) for user_id in data['member_ids']):
        return error_response("All member IDs must be integers", 400)
    if 'creator_id' not in data or not isinstance(data['creator_id'], int):
        return error_response("Creator ID is required and must be an integer", 400)

    creator_id = data['creator_id']
    member_ids = data['member_ids']

    # creator_id ni member_ids ga qo‘shish, lekin takrorlanmasligini ta'minlash
    all_members = set(member_ids)  # Takrorlanishni oldini olish uchun set ishlatamiz
    all_members.add(creator_id)  # creator_id ni qo‘shamiz

    try:
        group = Group(name=data['name'].strip())
        db.session.add(group)
        db.session.commit()

        for user_id in all_members:
            if not User.query.get(user_id):
                db.session.rollback()
                return error_response(f"User {user_id} not found", 404)
            member = GroupMembers(user_id=user_id, group_id=group.id)
            db.session.add(member)

        db.session.commit()
        logger.info(f"Group {group.name} created by user {creator_id}")
        return jsonify({'message': 'Group created', 'group_id': group.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating group: {str(e)}")
        return error_response(str(e), 500)

# 1:1 xabarlarni olish
@app.route('/api/messages/<int:user_id>/<int:receiver_id>', methods=['GET'])
def get_messages(user_id, receiver_id):
    try:
        messages = Messages.query.filter(
            ((Messages.sender_id == user_id) & (Messages.receiver_id == receiver_id)) |
            ((Messages.sender_id == receiver_id) & (Messages.receiver_id == user_id))
        ).filter(Messages.group_id == None).options(joinedload(Messages.reactions)).order_by(Messages.timestamp.asc()).all()

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

# Guruh xabarlarni olish
@app.route('/api/group_messages/<int:group_id>', methods=['GET'])
def get_group_messages(group_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return error_response("User ID is required as a query parameter", 400)

    try:
        messages = Messages.query.filter_by(group_id=group_id).options(joinedload(Messages.reactions)).order_by(Messages.timestamp.asc()).all()
        deleted_messages = {dm.message_id for dm in DeletedMessage.query.filter_by(user_id=user_id).all()}

        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'group_id': msg.group_id,
            'content': msg.content,
            'media_url': msg.media_url,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': MessageReadStatus.query.filter_by(message_id=msg.id, user_id=user_id).first().is_read if MessageReadStatus.query.filter_by(message_id=msg.id, user_id=user_id).first() else False,
            'reactions': [{'user_id': r.user_id, 'emoji': r.emoji} for r in msg.reactions]
        } for msg in messages if msg.id not in deleted_messages]), 200
    except Exception as e:
        logger.error(f"Error fetching group messages: {str(e)}")
        return error_response(str(e), 500)

# Media fayl yuklash
@app.route('/api/upload_media', methods=['POST'])
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
        logger.info(f"File {filename} uploaded")
        return jsonify({'media_url': f"/Uploads/{filename}"}), 200
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return error_response("Failed to upload file", 500)

# Socket.IO eventlari
@socketio.on('join')
def on_join(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')

    if not (receiver_id or group_id):
        emit('error', {'message': 'Invalid data: receiver_id or group_id required'})
        return

    room = get_room_name(user_id, receiver_id, group_id)
    join_room(room)
    emit('status', {'message': f'Joined room {room}'}, room=room)
    logger.info(f"User {user_id} joined room {room}")

@socketio.on('leave')
def on_leave(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')

    room = get_room_name(user_id, receiver_id, group_id)
    leave_room(room)
    emit('status', {'message': f'Left room {room}'}, room=room)
    logger.info(f"User {user_id} left room {room}")

@socketio.on('typing')
def handle_typing(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')

    user = User.query.get(user_id)
    if not user:
        emit('error', {'message': 'User not found'})
        return

    room = get_room_name(user_id, receiver_id, group_id)
    emit('typing', {'username': user.username, 'is_typing': True}, room=room, skip_sid=request.sid)
    logger.info(f"User {user_id} is typing in room {room}")

@socketio.on('send_message')
def handle_message(data):
    sender_id = data.get('sender_id')
    if not sender_id or not isinstance(sender_id, int):
        emit('error', {'message': 'Sender ID is required and must be an integer'})
        return

    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    content = data.get('content')
    media_url = data.get('media_url')

    if not (content or media_url):
        emit('error', {'message': 'Content or media_url is required'})
        return
    if content and not isinstance(content, str):
        emit('error', {'message': 'Content must be a string'})
        return
    if media_url and not isinstance(media_url, str):
        emit('error', {'message': 'Media URL must be a string'})
        return
    if receiver_id and not isinstance(receiver_id, int):
        emit('error', {'message': 'Receiver ID must be an integer'})
        return
    if group_id and not isinstance(group_id, int):
        emit('error', {'message': 'Group ID must be an integer'})
        return

    try:
        new_message = Messages(
            sender_id=sender_id,
            receiver_id=receiver_id,
            group_id=group_id,
            content=content,
            media_url=media_url
        )
        db.session.add(new_message)
        db.session.commit()

        if group_id:
            members = GroupMembers.query.filter_by(group_id=group_id).all()
            for member in members:
                if member.user_id != sender_id:
                    read_status = MessageReadStatus(message_id=new_message.id, user_id=member.user_id)
                    db.session.add(read_status)
            db.session.commit()

        room = get_room_name(sender_id, receiver_id, group_id)
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

        emit('notification', {'message': 'New message received', 'from_user_id': sender_id}, room=room)
        logger.info(f"Message sent by user {sender_id} to room {room}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending message: {str(e)}")
        emit('error', {'message': 'Failed to send message'})

@socketio.on('read_message')
def handle_read_message(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    message_id = data.get('message_id')
    if not isinstance(message_id, int):
        emit('error', {'message': 'Message ID must be an integer'})
        return

    message = Messages.query.get(message_id)
    if not message:
        emit('error', {'message': 'Message not found'})
        return

    try:
        if message.receiver_id == user_id:
            message.is_read = True
            db.session.commit()
        elif message.group_id:
            read_status = MessageReadStatus.query.filter_by(message_id=message_id, user_id=user_id).first()
            if read_status:
                read_status.is_read = True
                db.session.commit()

        room = get_room_name(message.sender_id, message.receiver_id, message.group_id)
        emit('message_read', {'message_id': message_id, 'is_read': True}, room=room)
        logger.info(f"Message {message_id} marked as read by user {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking message as read: {str(e)}")
        emit('error', {'message': 'Failed to mark message as read'})

@socketio.on('add_reaction')
def handle_reaction(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    message_id = data.get('message_id')
    emoji = data.get('emoji')

    if not isinstance(message_id, int):
        emit('error', {'message': 'Message ID must be an integer'})
        return
    if not isinstance(emoji, str) or len(emoji.strip()) == 0:
        emit('error', {'message': 'Emoji must be a non-empty string'})
        return

    message = Messages.query.get(message_id)
    if not message:
        emit('error', {'message': 'Message not found'})
        return

    try:
        reaction = Reaction(message_id=message_id, user_id=user_id, emoji=emoji.strip())
        db.session.add(reaction)
        db.session.commit()

        room = get_room_name(message.sender_id, message.receiver_id, message.group_id)
        emit('reaction_added', {'message_id': message_id, 'user_id': user_id, 'emoji': emoji}, room=room)
        logger.info(f"Reaction {emoji} added to message {message_id} by user {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding reaction: {str(e)}")
        emit('error', {'message': 'Failed to add reaction'})

@socketio.on('delete_message')
def handle_delete_message(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    message_id = data.get('message_id')
    delete_for_all = data.get('delete_for_all', False)

    if not isinstance(message_id, int):
        emit('error', {'message': 'Message ID must be an integer'})
        return
    if not isinstance(delete_for_all, bool):
        emit('error', {'message': 'delete_for_all must be a boolean'})
        return

    message = Messages.query.get(message_id)
    if not message or message.sender_id != user_id:
        emit('error', {'message': 'Unauthorized or message not found'})
        return

    try:
        if delete_for_all:
            db.session.delete(message)
        else:
            deleted_message = DeletedMessage(message_id=message_id, user_id=user_id)
            db.session.add(deleted_message)
        db.session.commit()

        room = get_room_name(message.sender_id, message.receiver_id, message.group_id)
        emit('message_deleted', {'message_id': message_id, 'delete_for_all': delete_for_all}, room=room)
        logger.info(f"Message {message_id} deleted by user {user_id}, for_all={delete_for_all}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting message: {str(e)}")
        emit('error', {'message': 'Failed to delete message'})

@socketio.on('edit_message')
def handle_edit_message(data):
    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, int):
        emit('error', {'message': 'User ID is required and must be an integer'})
        return

    message_id = data.get('message_id')
    new_content = data.get('new_content')

    if not isinstance(message_id, int):
        emit('error', {'message': 'Message ID must be an integer'})
        return
    if not isinstance(new_content, str) or len(new_content.strip()) == 0:
        emit('error', {'message': 'New content must be a non-empty string'})
        return

    message = Messages.query.get(message_id)
    if not message or message.sender_id != user_id:
        emit('error', {'message': 'Unauthorized or message not found'})
        return

    try:
        message.content = new_content.strip()
        db.session.commit()

        room = get_room_name(message.sender_id, message.receiver_id, message.group_id)
        emit('message_edited', {'message_id': message_id, 'new_content': new_content}, room=room)
        logger.info(f"Message {message_id} edited by user {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing message: {str(e)}")
        emit('error', {'message': 'Failed to edit message'})

@app.route('/api/block/<int:blocked_id>', methods=['POST'])
def block_user(blocked_id):
    data = request.get_json()
    if not data or 'blocker_id' not in data or not isinstance(data['blocker_id'], int):
        return error_response("Blocker ID is required and must be an integer", 400)

    blocker_id = data['blocker_id']
    if blocker_id == blocked_id:
        return error_response("Cannot block yourself", 400)

    if Block.query.filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first():
        return error_response("User already blocked", 400)

    try:
        block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        db.session.add(block)
        db.session.commit()
        logger.info(f"User {blocker_id} blocked user {blocked_id}")
        return jsonify({'message': 'User blocked'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error blocking user: {str(e)}")
        return error_response(str(e), 500)

@app.route('/api/unread_count/<int:user_id>', methods=['GET'])
def unread_count(user_id):
    try:
        cache_key = f"unread_count_{user_id}"
        try:
            cached_count = redis.get(cache_key)
            if cached_count:
                return jsonify({'unread_count': int(cached_count)}), 200
        except Exception as redis_error:
            logger.error(f"Redis error: {str(redis_error)}")
            # Redis ishlamasa, to‘g‘ridan-to‘g‘ri bazadan hisoblaymiz

        unread = Messages.query.filter(
            (Messages.receiver_id == user_id) & (Messages.is_read == False)
        ).count()
        try:
            redis.setex(cache_key, 300, unread)  # 5 daqiqa kesh
        except Exception as redis_error:
            logger.error(f"Redis set error: {str(redis_error)}")
        return jsonify({'unread_count': unread}), 200
    except Exception as e:
        logger.error(f"Error fetching unread count: {str(e)}")
        return error_response(str(e), 500)
