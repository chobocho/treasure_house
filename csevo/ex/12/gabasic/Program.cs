// 슬라이드 p12-v11-genattr — 제네릭 특성, C# 11.0
using System;

// before C# 11: the type travels as a System.Type argument
class TypeAttribute : Attribute
{
    public TypeAttribute(Type t) => ParamType = t;
    public Type ParamType { get; }
}

// C# 11: the type is a type argument
class GenericAttribute<T> : Attribute
{
    public Type ParamType => typeof(T);
}

class App
{
    [Type(typeof(string))]
    public static void Old() { }

    [Generic<string>]
    public static void New() { }

    static void Main()
    {
        var a = (TypeAttribute)Attribute.GetCustomAttribute(
            typeof(App).GetMethod("Old"), typeof(TypeAttribute));
        var b = (GenericAttribute<string>)Attribute.GetCustomAttribute(
            typeof(App).GetMethod("New"),
            typeof(GenericAttribute<string>));
        Console.WriteLine(a.ParamType + " " + b.ParamType);
        Console.WriteLine(b.GetType());
    }
}
