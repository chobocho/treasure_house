// 슬라이드 p15-v14-pe-gen — 생성기가 구현하는 partial 이벤트, C# 14
using System;
using System.Runtime.CompilerServices;

[AttributeUsage(AttributeTargets.Event)]
class WeakEventAttribute : Attribute { }

partial class Button
{
    [WeakEvent]
    public partial event Action<string> Clicked;   // written by hand

    public void Click() => RaiseClicked("click");
}

class Window
{
    readonly string title;
    public Window(string t) { title = t; }
    public void OnClick(string s) =>
        Console.WriteLine(title + ": " + s);
}

class Program
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    static void Attach(Button b, string title) =>
        b.Clicked += new Window(title).OnClick;

    static void Main()
    {
        var b = new Button();
        var kept = new Window("kept");
        b.Clicked += kept.OnClick;
        Attach(b, "dropped");
        b.Click();
        GC.Collect();
        GC.WaitForPendingFinalizers();
        b.Click();
        GC.KeepAlive(kept);
    }
}
