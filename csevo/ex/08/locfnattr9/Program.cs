// 슬라이드 p8-v7-locfn-attr9 — 지역 함수의 특성, C# 9.0
using System;
using System.Linq;
using System.Reflection;

class NoteAttribute : Attribute
{
    public string Text;
    public NoteAttribute(string t) { Text = t; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(Twice(4));

        [Note("helper")]
        static int Twice(int v) => v * 2;

        var m = typeof(App)
            .GetMethods(BindingFlags.NonPublic | BindingFlags.Static)
            .Single(x => x.Name.Contains("Twice"));
        Console.WriteLine(m.GetCustomAttribute<NoteAttribute>().Text);
    }
}
