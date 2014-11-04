import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

    def testGetEmptyPosts(self):
        """ Getting posts from an empty database"""
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data, [])

    def testGetPosts(self):
        """ Getting posts from a populated database """
        postA = models.Post(title="Title A", body=
            "Posting up over heeeere")
        postB = models.Post(title="Other title", body=
            "What a wonderful world")
        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")] 
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(postA["title"], "Title A")
        self.assertEqual(postA["body"], "Posting up over heeeere")

        postB = data[1]
        self.assertEqual(postB["title"], "Other title")
        self.assertEqual(postB["body"], "What a wonderful world")

    def testGetPost(self):
        """ Get a single post from a populated database """
        postA = models.Post(title="Title A", body=
            "Posting up over heeeere")
        postB = models.Post(title="Other title", body=
            "What a wonderful world")
        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data)
        self.assertEqual(post["title"], "Other title")
        self.assertEqual(post["body"], "What a wonderful world")

    def testGetNonExistentPost(self):
        """ Getting a single post which doesn't exist """
        response = self.client.get("/api/posts/1",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find post with id 1")

    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/posts", 
            headers = [("Accept", "application/xml")]
            )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], 
            "Request must accept application/json data")

    def testGetPostsWithTitle(self):
        """ Filtering posts by title """
        postA = models.Post(title="Post with green eggs", body="Just a test")
        postB = models.Post(title="Post with ham", body="Still a test")
        postC = models.Post(title="Post with green eggs and ham", body="Another test")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=ham",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with ham")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with green eggs and ham")
        self.assertEqual(post["body"], "Another test")

    def testGetPostsWithBody(self):
        """ Filtering posts by body """
        postA = models.Post(title="Post with green eggs", body="Just a test")
        postB = models.Post(title="Post with ham", body="Still a test")
        postC = models.Post(title="Post with green eggs and ham", body="Still testing")
        
        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?body_like=still",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with ham")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with green eggs and ham")
        self.assertEqual(post["body"], "Still testing")

    def testGetPostsWithTitleAndBody(self):
        """ Filtering posts by title and body """
        postA = models.Post(title="Green eggs and ham", body="A post by Sam I Am about my favorite foods")
        postB = models.Post(title="Green fish blue fish", body="A post about Sam I Am's fish bowl")
        postC = models.Post(title="Green is my favorite color", body="A post by James about how much I love the color green")
        postD = models.Post(title="The Cat in the Hat", body="A post by Sam I Am about my greatest rival for power")

        session.add_all([postA, postB, postC, postD])
        session.commit()

        response = self.client.get("/api/posts?title_like=green&body_like=Sam",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Green eggs and ham")
        self.assertEqual(post["body"], "A post by Sam I Am about my favorite foods")

        post = posts[1]
        self.assertEqual(post["title"], "Green fish blue fish")
        self.assertEqual(post["body"], "A post about Sam I Am's fish bowl")

    def testPostPost(self):
        """ Posting a new post """
        data = {
        "title": "Example Post",
        "body": "Just a test"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
           headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
            "/api/posts/1")

        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")



if __name__ == "__main__":
    unittest.main()
