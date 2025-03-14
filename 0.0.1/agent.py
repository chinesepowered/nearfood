from nearai.agents.environment import Environment


def run(env: Environment):
    # Your agent code here
    prompt = {"role": "system", "content": "Crawl events and find food"}
    result = env.completion([prompt] + env.list_messages())
    env.add_reply(result)
    env.request_user_input()


run(env)
