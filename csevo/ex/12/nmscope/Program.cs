// 슬라이드 p12-v11-nameof — nameof 가 보는 이름의 범위, C# 11.0
using System;
using System.Reflection;

class NoteAttribute : Attribute
{
    public NoteAttribute(string text) => Text = text;
    public string Text { get; }
}

delegate void Handler([Note(nameof(sender))] object sender);

class App
{
    [Note(nameof(T))]                                  // type parameter
    static void Generic<T>() { }

    static void Pair(int first, [Note(nameof(first))] int second) { }

    static void Main()
    {
        [Note(nameof(n))] static int Local(int n) => n; // local func
        Func<int, int> lam = [Note(nameof(x))] (x) => x; // lambda

        Show(typeof(App).GetMethod("Generic", BindingFlags.Static
            | BindingFlags.NonPublic));
        Show(typeof(App).GetMethod("Pair", BindingFlags.Static
            | BindingFlags.NonPublic).GetParameters()[1]);
        Show(typeof(Handler).GetMethod("Invoke").GetParameters()[0]);
        Show(lam.Method);
        Console.WriteLine(Local(1));
    }

    static void Show(ICustomAttributeProvider p) =>
        Console.WriteLine(((NoteAttribute)p.GetCustomAttributes(
            typeof(NoteAttribute), false)[0]).Text);
}
