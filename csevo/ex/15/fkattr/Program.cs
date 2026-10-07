// 슬라이드 p15-v14-fk-attr — [field: …] 특성, C# 14
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.Field)]
class NoteAttribute : Attribute
{
    public NoteAttribute(string text) { Text = text; }
    public string Text { get; }
}

class C
{
    [field: Note("lazy cache")]
    public string Name => field ??= "n";

    [field: Note("clamped")]
    public int Level { get; set => field = Math.Min(value, 9); }

#if BAD
    [field: Note("no field")]
    public string Plain => "p";
#endif
}

class Program
{
    static void Main()
    {
        var flags = BindingFlags.NonPublic | BindingFlags.Instance;
        foreach (var f in typeof(C).GetFields(flags))
            Console.WriteLine(f.Name + " -> "
                + f.GetCustomAttribute<NoteAttribute>().Text);
    }
}
