// 슬라이드 p12-v11-nameof-old — 게이트가 없는 기능, C# 11.0
using System;
using System.Reflection;

class NoteAttribute : Attribute
{
    public NoteAttribute(string text) { Text = text; }
    public string Text;
}

class App
{
    [Note(nameof(T))]
    static void Generic<T>() { }

    static void Main()
    {
        MethodInfo m = typeof(App).GetMethod("Generic",
            BindingFlags.Static | BindingFlags.NonPublic);
        object[] a = m.GetCustomAttributes(typeof(NoteAttribute),
            false);
        Console.WriteLine(((NoteAttribute)a[0]).Text);
    }
}
