// 슬라이드 p3-v2-accessor-lookup — 숨긴 속성의 private set, C# 2.0
using System;

class A
{
    public string Text
    {
        get { return "hello"; }
        set { }
    }
}

class B : A
{
    string text = "goodbye";
    public new string Text
    {
        get { return text; }
        protected set { text = value; }
    }
}

class App
{
    static void Main()
    {
        B b = new B();
        b.Text = "howdy";                // B.Text hides A.Text
        Console.WriteLine(b.Text);
    }
}
