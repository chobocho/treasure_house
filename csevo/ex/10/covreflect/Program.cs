// 슬라이드 p10-v9-cov-meta — 공변 반환의 메타데이터, C# 9.0
using System;
using System.Linq;
using System.Reflection;

class Animal { public virtual Animal Clone() => new Animal(); }
class Tiger : Animal { public override Tiger Clone() => new Tiger(); }

class App
{
    static void Main()
    {
        foreach (MethodInfo m in typeof(Tiger).GetMethods()
                     .Where(m => m.Name == "Clone"))
        {
            Console.WriteLine("{0}.Clone : {1,-6} newslot={2} base={3}",
                m.DeclaringType.Name, m.ReturnType.Name,
                m.Attributes.HasFlag(MethodAttributes.NewSlot),
                m.GetBaseDefinition().DeclaringType.Name);
            foreach (var a in m.GetCustomAttributesData())
                Console.WriteLine("  [" + a.AttributeType.Name + "]");
        }
        MethodInfo one = typeof(Tiger).GetMethod("Clone");
        Console.WriteLine("GetMethod: " + one.ReturnType.Name);
    }
}
