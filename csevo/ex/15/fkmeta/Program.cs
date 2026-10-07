// 슬라이드 p15-v14-fk-meta — 뒷받침 필드의 메타데이터, C# 14
using System;
using System.Diagnostics;
using System.Linq;
using System.Reflection;

class C
{
    public int Auto { get; set; }
    public int Clamped
    { get => field; set => field = Math.Max(0, value); }
    public string Lazy => field ??= "computed";
    public int Fixed { get; }
    public int Plain => 42;                     // no field used
    public object Checked
    {
        get { Debug.Assert(field is null); return null; }
    }
}

class Program
{
    static void Main()
    {
        var flags = BindingFlags.NonPublic | BindingFlags.Instance;
        foreach (var f in typeof(C).GetFields(flags)
                     .OrderBy(f => f.MetadataToken))
        {
            var names = f.GetCustomAttributes(false)
                .Select(a => a.GetType().Name.Replace("Attribute", ""));
            Console.WriteLine(f.Name.PadRight(26)
                + (f.IsInitOnly ? "initonly " : "")
                + string.Join(",", names));
        }
    }
}
