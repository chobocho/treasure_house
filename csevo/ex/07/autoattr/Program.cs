// 슬라이드 p7-v6-auto-attr — 숨은 필드에 특성 붙이기, C# 7.3
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.Field)]
class NoteAttribute : Attribute
{
    public string Text;
    public NoteAttribute(string text) { Text = text; }
}

class Person
{
    [field: Note("on the backing field")]
    public string Name { get; set; }
}

class Program
{
    static void Main()
    {
        FieldInfo f = typeof(Person).GetField("<Name>k__BackingField",
            BindingFlags.NonPublic | BindingFlags.Instance);
        NoteAttribute a = f.GetCustomAttribute<NoteAttribute>();
        Console.WriteLine(a == null ? "none" : a.Text);
        PropertyInfo p = typeof(Person).GetProperty("Name");
        Console.WriteLine(p.GetCustomAttributes(false).Length);
    }
}
