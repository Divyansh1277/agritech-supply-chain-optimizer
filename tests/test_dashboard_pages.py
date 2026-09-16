import pytest
from streamlit.testing.v1 import AppTest

def test_all_pages_render_without_exception():
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception, f"Executive Overview failed with exception: {at.exception}"

    core_pages = [
        "Executive Overview",
        "Price & MSP",
        "Arrivals & Anomalies",
        "Weather Impact",
        "Logistics",
        "Data Quality"
    ]

    # Test all 6 core dashboard pages
    for p in core_pages:
        at.sidebar.radio(key="nav_page").set_value(p).run()
        assert not at.exception, f"Page '{p}' threw an exception: {at.exception}"
        print(f"Page '{p}' passed successfully.")

    # Test circular AI button
    at.button("ai_circle_btn").click().run()
    assert not at.exception, f"AI Agent circle button threw an exception: {at.exception}"
    print("Circular 'AI' button activated AI Agent view successfully.")

    # Test return from AI button
    at.button("btn_exit_ai").click().run()
    assert not at.exception, f"Exit AI Agent threw an exception: {at.exception}"
    print("Return to Dashboard from AI Agent passed successfully.")

    # Test with compare_previous enabled
    at.sidebar.toggle(key=None).set_value(True).run()
    for p in core_pages:
        at.sidebar.radio(key="nav_page").set_value(p).run()
        assert not at.exception, f"Page '{p}' with compare_previous threw: {at.exception}"
        print(f"Page '{p}' (with compare) passed successfully.")

    # Test circular AI button with compare enabled
    at.button("ai_circle_btn").click().run()
    assert not at.exception, f"AI Agent with compare threw: {at.exception}"
    print("Circular 'AI' button with compare passed successfully.")

if __name__ == "__main__":
    test_all_pages_render_without_exception()
