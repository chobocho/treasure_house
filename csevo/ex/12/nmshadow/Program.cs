// 슬라이드 p12-v11-nameof-shadow — nameof 안에서만 보인다, C# 11.0
using System;
using System.Reflection;

class NoteAttribute : Attribute
{
    public NoteAttribute(string text) => Text = text;
    public string Text { get; }
}

class App
{
    const string Data = "the constant";

    [Note(Data)]                         // outside nameof: the constant
    static void A(int[] Data) { }

    [Note(nameof(Data.Rank))]            // int[] has Rank, string not
    static void B(int[] Data) { }

    static void Main()
    {
        foreach (string name in new[] { "A", "B" })
        {
            MethodInfo m = typeof(App).GetMethod(name,
                BindingFlags.Static | BindingFlags.NonPublic);
            Console.WriteLine(name + ": "
                + m.GetCustomAttribute<NoteAttribute>().Text);
        }
    }
}
