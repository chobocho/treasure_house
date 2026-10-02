// 슬라이드 p8-v7_3-fieldattr — 자동 속성의 뒷받침 필드에 특성, C# 7.3
using System;
using System.Linq;
using System.Reflection;

[Serializable]
class Account
{
    public string Name { get; set; }

    [field: NonSerialized]               // goes to the hidden field
    public string Secret { get; set; }
}

class App
{
    static void Main()
    {
        var fields = typeof(Account)
            .GetFields(BindingFlags.Instance | BindingFlags.NonPublic)
            .OrderBy(f => f.Name);
        foreach (var f in fields)
        {
            var names = f.GetCustomAttributes(false)
                .Select(a => a.GetType().Name.Replace("Attribute", ""));
            Console.WriteLine(f.Name);
            Console.WriteLine("  [" + string.Join(", ", names) + "]");
        }
    }
}
