// 슬라이드 p5-v4-named-attr — 특성의 두 가지 '이름 붙인' 인수, C# 4.0
using System;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = true)]
class NoteAttribute : Attribute
{
    public NoteAttribute(string text, int level = 0)
    {
        Text = text; Level = level;
    }
    public string Text;
    public int Level;
    public string Owner;
}

[Note("one", Owner = "property-style, C# 1")]
[Note("two", level: 2)]
class Target { }

class Program
{
    static void Main()
    {
        Type t = typeof(Target);
        foreach (NoteAttribute n in
                 t.GetCustomAttributes(typeof(NoteAttribute), false))
        {
            Console.WriteLine(n.Text + " level=" + n.Level
                              + " owner=" + n.Owner);
        }
    }
}
