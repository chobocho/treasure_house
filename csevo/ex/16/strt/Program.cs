// 슬라이드 p16-st-rt-meta — 런타임이 알아야 하는 언어 기능, C# 14
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

interface IShape
{
    static abstract IShape Unit();           // C# 11: static abstract
    string Name() => "shape";                // C# 8: body in interface
}
class Animal { public virtual Animal Make() => new Animal(); }
class Cat : Animal { public override Cat Make() => new Cat(); } // C# 9
ref struct Holder { public ref int Slot; }   // C# 11: ref field
static class G
{
    public static void M<T>() where T : allows ref struct { } // C# 13
}

class Program
{
    static void Main()
    {
        MethodInfo unit = typeof(IShape).GetMethod("Unit");
        MethodInfo name = typeof(IShape).GetMethod("Name");
        MethodInfo make = typeof(Cat).GetMethod("Make");
        FieldInfo slot = typeof(Holder).GetField("Slot");
        Type t = typeof(G).GetMethod("M").GetGenericArguments()[0];
        Show("static abstract", unit.IsStatic && unit.IsAbstract,
             RuntimeFeature.VirtualStaticsInInterfaces);
        Show("interface body", !name.IsAbstract,
             RuntimeFeature.DefaultImplementationsOfInterfaces);
        Show("covariant return", make.IsDefined(
                 typeof(PreserveBaseOverridesAttribute)),
             RuntimeFeature.CovariantReturnsOfClasses);
        Show("ref field", slot.FieldType.IsByRef,
             RuntimeFeature.ByRefFields);
        Show("allows ref struct", t.GenericParameterAttributes
                 .HasFlag(GenericParameterAttributes.AllowByRefLike),
             RuntimeFeature.ByRefLikeGenerics);
    }
    static void Show(string what, bool mark, string feature) =>
        Console.WriteLine("{0,-18} {1,-5} {2,-34} {3}", what, mark,
            feature, RuntimeFeature.IsSupported(feature));
}
