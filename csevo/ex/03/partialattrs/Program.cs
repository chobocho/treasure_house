// 슬라이드 p3-v2-partial-attrs — 조각의 특성을 합친다, C# 2.0
using System;
using System.ComponentModel;

[AttributeUsage(AttributeTargets.Class)]
class TagAttribute : Attribute
{
    public string Text;
    public TagAttribute(string text) { Text = text; }
}

[Tag("by hand")]
partial class Settings { }

class App
{
    static void Main()
    {
        Type t = typeof(Settings);
        Type dt = typeof(DescriptionAttribute);
        DescriptionAttribute d = (DescriptionAttribute)
            Attribute.GetCustomAttribute(t, dt);
        TagAttribute tag = (TagAttribute)
            Attribute.GetCustomAttribute(t, typeof(TagAttribute));
        Console.WriteLine("description: " + d.Description);
        Console.WriteLine("tag: " + tag.Text);
    }
}
